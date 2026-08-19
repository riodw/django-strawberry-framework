# Build: Slice 1a — Planned contract vs HEAD (card `DONE-024-0.0.7`)

Spec reference: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` (1,618-byte stub; carries no contract — the recovered inputs below are the contract)
Status: final-accepted

Recovered input contract (read-only, never restored to the tree):

- `docs/builder/temp-tests/PLAN-024.md` — the deleted `docs/PLAN-trac-37064-database-teardown.md` (deleted at `d1d19ca2`, 2026-05-27).
- `docs/builder/temp-tests/TEMP-024.md` — the deleted `docs/TEMP-trac-37064-test-plan.md` (same commit).

HEAD at audit time: `36cd1925`.

## Plan (Worker 1)

### DRY analysis

Not applicable; this is a read-only audit cohort. No source was edited, no helper introduced.

### Implementation steps

Read-only walk of the recovered contract against HEAD. **Seven** populations, each measured before it was
walked (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`). The word
was "Six" in pass 1 against a seven-row table — re-counted in pass 2, along with every count in the table
itself, all of which reproduce:

| Population | Count | How measured |
|---|---|---|
| `PLAN-024.md` `## Definition of done` numbered items | 9 | `awk '/^## Definition of done/,/^## Out of scope/' … \| grep -c "^[0-9]\+\. "` |
| Planned tests in `### tests/test_django_patches.py (new)` | 10 | `awk '/### \`tests\/test_django_patches.py\` \(new\)/,/^### \`tests\/test_apps.py\`/' … \| grep -c "^[0-9]"` |
| Planned tests in the Phase-4 `tests/test/test_wrap.py` line | 5 | the line's own parenthesised list, enumerated below |
| `TEMP-024.md` `## Required Tests` numbered items | 3 | `awk '/^## Required Tests/,/^## Efficient/' … \| grep -c "^[0-9]\+\. "` |
| `PLAN-024.md` `## Decisions made during implementation` bullets | 5 | `awk '/^## Decisions made/,/^## Risks/' … \| grep -c "^- \*\*"` |
| `PLAN-024.md` `## Risks and open questions` bullets | 4 | `awk '/^## Risks and open/,/^## Definition of done/' … \| grep -c "^- \*\*"` |
| `PLAN-024.md` `## Out of scope for this plan` bullets | 3 | `awk '/^## Out of scope/,/^## Update:/' … \| grep -c "^- "` |

Tests present at HEAD, measured with `grep -c "^def test_"`: `tests/test_django_patches.py` **21**,
`tests/testing/test_wrap.py` **7**, `tests/test_apps.py` **8** — 36 total, matching the focused run's
`36 passed`.

**These seven are not all of the recovered documents' populations.** Five more went un-walked in pass 1 —
`TEMP-024.md`'s four non-enumerated `##` sections and `PLAN-024.md`'s Phase-4 `**Landed**` list (5
bullets) — and all five are walked in `#### 7` below, folded in from the Worker 3 review pass.

### Test additions / updates

None. This pass is read-only on all source and tests.

### Implementation discretion items

None.

### Spec slice checklist (verbatim)

The active spec is a stub with no `## Slice checklist`. No boxes to tick; this cohort's contract is the
dispatch's six numbered walks, all completed below.

---

## Build report (Worker 2)

### Files touched

- `docs/builder/bld-slice-1a-024-planned_vs_head.md` — this artifact (new).
- `docs/builder/worker-memory/worker-2-024.md` — one appended memory entry (gitignored).

No `.py` file, no spec file, no baseline-dirty file was modified. `git status --short` after the pass
shows only this artifact as new under `docs/builder/`; every other entry is the baseline-dirty set the
build plan lists.

### Tests added or updated

None (read-only pass).

### Validation run

- `uv run ruff format --check <8 subject files>` — pass (`8 files already formatted`).
- `uv run ruff check <same 8 files>` — pass (`All checks passed!`).
- `uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov -q`
  — **36 passed in 1.51s**, 8 xdist workers, `django: version: 6.1, settings: config.test_settings`.
  No red row. No `--cov*` flag used.
- No write-mode ruff, no `ruff --fix`, no reformat.

The subject files, all confirmed present:
`django_strawberry_framework/_django_patches.py` (406 lines), `django_strawberry_framework/apps.py`,
`django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/testing/__init__.py`,
`django_strawberry_framework/conf.py`, `tests/test_django_patches.py`, `tests/testing/test_wrap.py`,
`tests/test_apps.py`. The dispatch's surface list was **incomplete in one place**: the plan's
`django_strawberry_framework/test/` and `tests/test/` paths no longer exist — both were renamed at
`e145ba36` (see walk row P-1).

### Failability proofs

None; this pass introduced no boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Owned by Slice 1b per the plan's declaration. The installed interpreter here resolves **Django 6.1**
(pytest header, quoted above), which means the live suite exercises only the
`_CONNECTION_FEATURE_REMOVE_DATABASES_FAILURES_SOURCE` branch of the audited-body set; the
`_CLASS_ATTRIBUTE_…` branch is reached only synthetically. That is exactly the gap the plan's floor
declaration exists to close — flagged here for Slice 1b, not acted on.

### Planned-contract walk

Read-only HEAD reference used throughout, per `docs/builder/BUILD.md`:

```
git show 300e2811:django_strawberry_framework/_django_patches.py > /tmp/dsf-024-patches-ship.py
git show d1d19ca2^:django_strawberry_framework/_django_patches.py > /tmp/dsf-024-patches-plan.py
git show eb2a1764:django_strawberry_framework/_django_patches.py  > /tmp/dsf-024-patches-eb.py
git show 300e2811:django_strawberry_framework/__init__.py         > /tmp/dsf-024-init-ship.py
git show 61973f8d:django_strawberry_framework/__init__.py         > /tmp/dsf-024-init-p4.py
wc -l /tmp/dsf-024-patches-ship.py django_strawberry_framework/_django_patches.py
#   91 /tmp/dsf-024-patches-ship.py
#  406 django_strawberry_framework/_django_patches.py
diff /tmp/dsf-024-patches-ship.py django_strawberry_framework/_django_patches.py | grep -c "^[<>]"   # 369
diff /tmp/dsf-024-init-ship.py /tmp/dsf-024-init-p4.py && echo identical                             # identical
```

**The commit population, re-derived (pass 2).** The first pass built this table from a `--all` log and
called the result "after the ship". Both halves were wrong, and the derivation was the cause, so the
derivation is restated here and the table rebuilt from it rather than patched in place:

```shell
git log --oneline -S'_remove_databases_failures' -- django_strawberry_framework/ tests/        # 10
git log --all --oneline -S'_remove_databases_failures' -- django_strawberry_framework/ tests/  # 23
```

`--all` reaches this machine's local object store, which carries pre-rewrite duplicates of commits that
were later rewritten on `main` (this repo is worked on by concurrent sessions and its history gets
rewritten). A "dedupe" step over that population keeps whichever duplicate it sees first, so it swept
orphans **in**. The population used from here on is the one a fresh clone can reproduce: the union of
`git log --follow` over the six surface files, each member proved HEAD-reachable with
`git merge-base --is-ancestor <sha> HEAD`.

```shell
for f in django_strawberry_framework/_django_patches.py django_strawberry_framework/testing/_wrap.py \
         django_strawberry_framework/apps.py tests/test_django_patches.py \
         tests/testing/test_wrap.py tests/test_apps.py; do
  git log --format=%h --follow -- $f; done | sort -u | wc -l          # 23
# minus b972cd84 / dfa035b4 (both 2026-05-21, apps.py + tests/test_apps.py only, and
# they predate the patch: the ship is 300e2811, 2026-05-23)          -> 21 surface commits
```

**21 commits touch the Trac #37064 surface, and 6 of them are inside tag `0.0.7`** (`72f6cd9b`), so
"the commits that moved this surface after the ship" was never the right heading for the first five
rows. In-tag membership measured per commit with `git merge-base --is-ancestor <sha> 0.0.7`:

| Commit | Date | Release | What it did to this surface |
|---|---|---|---|
| `300e2811` | 2026-05-23 | in `0.0.7` | Ship: patch installed on `TransactionTestCase`, `_PATCH_APPLIED` first-call-wins flag. `tests/test_django_patches.py` created with 6 tests. |
| `893465a5` | 2026-05-23 | in `0.0.7` | `_django_patches.py` docstring only (+60/-6): the `django-debug-toolbar` ecosystem precedent and the wrap-time/unwrap-time framing. No executable line. |
| `61973f8d` | 2026-05-23 | in `0.0.7` | Phase 4: `django_strawberry_framework/test/_wrap.py` + `tests/test/test_wrap.py` (4 tests), GLOSSARY entries. |
| `7014125a` | 2026-05-26 | in `0.0.7` | Retarget to `SimpleTestCase`; guarded `_DatabaseFailure` import + `_is_database_failure`; `_PATCH_APPLIED` -> `_patch_is_installed()`; `TypeError` guard in the wrap helper. Tests 6 -> 10 and, in the wrap file, 4 -> 6. **This is the state PLAN-024/TEMP-024 as recovered describe** — see the upper-bound measurement below. |
| `744fd28d` | 2026-05-26 | in `0.0.7` | `_missing_symbol_logged` sentinel so the missing-symbol INFO fires once (the `7014125a` docstring promised "a single INFO-level notice" while `apply()` logged on every call); non-callable example in the helper's `Raises:` block corrected. Tests 10 -> 11. |
| `e82df83d` | 2026-05-26 | in `0.0.7` | Adds the `_patch_is_installed()` `installed is None` branch test — the **12th** test, tests 11 -> 12. Not in the plan's list of 10. |
| `52d97ec0` | 2026-05-30 | post-tag | `tests/test_django_patches.py` layout only: one `assert` re-wrapped for line-length 100 / trailing-comma. |
| `e145ba36` | 2026-06-01 | post-tag | `test/` -> `testing/` rename (package **and** `tests/`), because `test` shadows the stdlib `test` package. |
| `b8a8a6e0` | 2026-06-01 | post-tag | `testing/_wrap.py` docstring only: RST subsection folded into a bold run; the example gains its missing `TransactionTestCase` import. |
| `7cc163db` | 2026-06-10 | post-tag | ASCII-only sweep across all six files (34 insertions / 34 deletions). One executable string: the `logger.info` message's em-dash. |
| `4a25bf42` | 2026-06-12 | post-tag | Module summary first lines for `_django_patches.py`, `apps.py`, `testing/_wrap.py` (3 lines). These render into `docs/TREE.md`. |
| `7c2a63ed` | 2026-06-12 | post-tag | Same, for the three test modules' summary lines (3 lines). |
| `c7cb5f5c` | 2026-06-18 | post-tag | Global `APPLY_UPSTREAM_PATCHES` gate added to this `apply()` alongside two new sibling patch modules; `ready()` goes from one applier to three. Adds `test_apply_no_ops_when_toggle_disabled`, tests 12 -> 13. |
| `48f9f65d` | 2026-07-11 | post-tag | **The fail-loud reversal.** `_original_remove_databases_failures` captured at import; `_validate_upstream_shape()` (tiers 1-2) raises `RuntimeError`; `logger`, `logger.info` and `_missing_symbol_logged` **deleted**; `test_apply_no_ops_when_database_failure_symbol_missing` and `test_apply_logs_missing_symbol_notice_only_once` deleted, `…_fails_loudly_when_database_failure_symbol_missing` and `…_fails_loudly_when_upstream_method_signature_changes` added. Tests 13 -> 13 (-2 / +2). Its subject ("Refactor subsystem clear registration and handling") names the type registry and says nothing about this file. |
| `0d655bde` | 2026-07-13 | post-tag | Tier 3, the body pin (`_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` + `textwrap.dedent(inspect.getsource(...))`, unreadable source treated as drift); per-dependency `{"django": False}` gating via `conf.upstream_patches_enabled("django")` (the `conf.py` half is `a62d6dca`, same day); every drift message names the escape hatch; the retirement test switched to the live import-time capture. Tests 13 -> 17. |
| `136c5476` | 2026-07-13 | post-tag | `tests/test_apps.py` pins `ready()`'s three-applier dispatch deterministically; `apps.py` docstrings stop repeating each module's bug inventory. |
| `5a74d803` | 2026-07-30 | post-tag | `tests/test_apps.py` + `tests/test_django_patches.py` comment prose only: review bookkeeping stripped. |
| `eb2a1764` | 2026-08-06 | post-tag | Django 6.1 deleted `SimpleTestCase._disallowed_connection_methods`; the single pinned body matched neither shape and **`ready()` raised, so the package refused to boot on 6.1**. Body pin becomes a 2-element audited set; `_disallowed_connection_methods()` added. Tests 17 -> 20. |
| `18550f5d` | 2026-08-16 | post-tag | Reload-safe capture (the two attribute-name constants `_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE`, stamped onto the replacement function and read back against the `_PATCH_OWNER` owner *value*); discriminator changed from `hasattr(cls, …)` to the validated body source. Tests 20 -> 21. |
| `f7fbead4` | 2026-08-16 | post-tag | `safe_wrap_connection_method`'s `TypeError` message stops interpolating the wrapper (a hostile `__repr__` could replace the intended exception). Wrap tests 6 -> 7. |
| `36cd1925` | 2026-08-18 | post-tag | `tests/test_apps.py` comment prose only (HEAD at audit time). |

Test-count progression for `tests/test_django_patches.py`, measured per commit with
`git show "<sha>:tests/test_django_patches.py" | grep -c '^def test_'`:
**6** (`300e2811`) -> **10** (`7014125a`) -> **11** (`744fd28d`) -> **12** (`e82df83d`) -> **13**
(`c7cb5f5c`) -> **13** (`48f9f65d`, two deleted and two added) -> **17** (`0d655bde`) -> 17
(`136c5476`) -> **20** (`eb2a1764`) -> **21** (`18550f5d`, and HEAD).

#### 1. Definition of done (9 items)

| # | Planned item (quoted) | Verdict | Evidence | What changed |
|---|---|---|---|---|
| 1 | "`django_strawberry_framework/_django_patches.py` exists with `apply()`, `_patched_remove_databases_failures`, and the rationale docstring." | **holds** | `django_strawberry_framework/_django_patches.py::apply`, `…::_patched_remove_databases_failures`, module docstring `#"Defensive patches for upstream Django bugs, applied at app load."` | Module grew 91 -> 406 lines; the three named artifacts are all present and still carry the ecosystem-precedent rationale. |
| 2 | "`django_strawberry_framework/apps.py` ships a `ready()` body that imports and calls `apply()`." | **holds** | `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready #"apply_django()"` | `ready()` now dispatches **three** appliers (`apply_django()`, `apply_strawberry()`, `apply_cross_web()`) behind function-local imports; the Django one is first. |
| 3 | "`tests/test_django_patches.py` exists with the **10 regression tests** above" | **superseded (superset, one member reversed)** | `tests/test_django_patches.py`, 21 `^def test_` | 9 of the 10 planned tests survive by name and assertion; #10 was deliberately inverted (row T-10). 11 tests were added after the plan. |
| 4 | "`tests/test_apps.py` allows `ready` and pins its presence via `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`." | **holds** | `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`; `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes #"``ready`` is deliberately absent from this set"` | The forbidden set is now `{label, default_auto_field, default}` — `ready` absent, with a comment saying why. A stronger dispatch test was added later: `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely`. |
| 5 | "The repo-root `conftest.py` workaround has been deleted." | **holds — vacuously, and for a stronger reason than a token search can give** | `git log --all --oneline --diff-filter=D -- conftest.py tests/conftest.py` -> **empty: no `conftest.py` was ever deleted in this repo, on any ref**. `git log --oneline -- conftest.py` -> **2 commits**, the earliest `57cbd32a` (2026-07-07), i.e. the only repo-root `conftest.py` that has ever existed was created six weeks *after* this card shipped | The item is not "the workaround was deleted" but "there was never a workaround here to delete" — the deletion-filter evidence establishes that directly, where the `-S'databases = "__all__"'` pickaxe the first pass used could only establish that one spelling of it never appeared. The widening workaround lived in `django-graphene-filters`. The repo-root `conftest.py` at HEAD is the Postgres tier's (`pg` marker, stray-connection tracking) and has nothing to do with this card. |
| 6 | "Full suite verification remains maintainer-triggered for this pass" | **holds (n/a to this cohort)** | — | This cohort ran the dispatch-authorised focused scope only: 36 passed. |
| 7 | "`uv run ruff format --check .` and `uv run ruff check .` both pass." | **holds, scoped** | see `### Validation run` | Verified read-only over the 8 subject files rather than `.` (a repo-wide claim would cover a concurrent session's dirty files, which this cohort cannot attest to). |
| 8 | "`__all__` in `django_strawberry_framework/__init__.py` is unchanged." | **holds as the card's claim — "unchanged *by this card*", not unchanged since** | `diff /tmp/dsf-024-init-ship.py /tmp/dsf-024-init-p4.py` -> identical (neither ship commit touched the root `__init__.py`); AST walk of the `__all__` assignment in both blobs -> **8 names at `300e2811`, 37 at HEAD**; the same walk filtered for `wrap` / `patch` / `testing` at HEAD -> **[]** | The list has changed a great deal since the ship — it is the package's whole public surface and grows every release — so an unqualified "unchanged" paired with today's count would read as a claim about the list itself. What this card owns is the narrower true statement: **no symbol from this work ever entered the root `__all__`**, at ship or since. The public helper is exported from `django_strawberry_framework.testing.__all__` only. The 8 -> 37 movement belongs to other cards and is not this card's to state. |
| 9a | "`KANBAN.md` — add a `DONE-NNN-0.0.X` card" | **holds (decided)** | `KANBAN.md #"DONE-024-0.0.7 - Django Trac #37064 hardening + \`safe_wrap_connection_method\`"` (card body at the `django_trac_37064_hardening_safe_wrap_connection_method` anchor) | Card exists, `done`, with the spec FK target. |
| 9b | "`CHANGELOG.md` — append a bullet under `### Fixed` for the version this ships in." | **superseded (landed under `### Added`), and the wording is now false in two places** | `CHANGELOG.md #"\`Django Trac #37064 hardening\` — package-level defensive patch"`, which sits under `## [0.0.7] - 2026-05-27` -> `### Added` | Two claims in that bullet are false at HEAD: "no settings key" (the patch is gated by `APPLY_UPSTREAM_PATCHES`) and "a log-once sentinel suppresses repeated missing-symbol notices" (the sentinel arrived at `744fd28d` and was retired at `48f9f65d`; there is no logger in the module at HEAD — `grep -c logger django_strawberry_framework/_django_patches.py` -> 0). Recorded as a deferred-work item; `CHANGELOG.md` is baseline-dirty and out of scope for this cycle. |
| 9c | "**Version target** — `0.0.7` joint cut … or `0.0.8`? Maintainer's call." | **holds (decided: `0.0.7`)** | `KANBAN.md #"0.0.7\` shipped 2026-05-27 with seven cards"`, which names `DONE-024-0.0.7`; GLOSSARY status rows read `shipped (0.0.7)` | Resolved in favour of the joint `0.0.7` cut. |

#### 2. The 15 named regression tests

**T-1..T-10 — `PLAN-024.md` `### tests/test_django_patches.py (new)`.** Each planned sentence was read
against the HEAD body, not matched on name.

| # | Planned test and its sentence | Verdict | HEAD site |
|---|---|---|---|
| T-1 | `test_apply_is_idempotent` — "pins the idempotency contract" | **holds** | `tests/test_django_patches.py::test_apply_is_idempotent` — asserts `_patch_is_installed() is True` after two `apply()` calls. (The ship commit asserted the retired `_PATCH_APPLIED is True`; the plan already describes the post-`7014125a` form.) |
| T-2 | `test_apply_reinstalls_when_class_attribute_reverted` — "pins the self-healing re-install contract" | **holds** | `tests/test_django_patches.py::test_apply_reinstalls_when_class_attribute_reverted` — installs a foreign classmethod, asserts `False`, re-applies, asserts `True`, restores in `finally`. |
| T-3 | `test_patch_is_installed_on_simple_test_case` — "`…__func__` is `_patched_remove_databases_failures`" | **holds** | `tests/test_django_patches.py::test_patch_is_installed_on_simple_test_case` — assertion is literally that identity check. |
| T-4 | `test_patch_is_inherited_by_transaction_test_case` | **holds** | `tests/test_django_patches.py::test_patch_is_inherited_by_transaction_test_case` |
| T-5 | `test_patch_is_inherited_by_test_case` | **holds** | `tests/test_django_patches.py::test_patch_is_inherited_by_test_case` |
| T-6 | `test_patched_remove_databases_failures_unwraps_a_real_wrapper` — "when the method IS a `_DatabaseFailure`, the patched code unwraps it exactly as upstream does" | **holds** | `tests/test_django_patches.py::test_patched_remove_databases_failures_unwraps_a_real_wrapper` — still `_DatabaseFailure(sentinel, …)` -> assert `connection.cursor is sentinel`. Construction moved behind the local `_database_failure()` helper, which `pytest.skip`s if the private symbol is gone. |
| T-7 | `test_patched_remove_databases_failures_skips_non_wrapper_methods` — "the Trac #37064 fix proper … leaves it alone and does NOT raise" | **holds** | `tests/test_django_patches.py::test_patched_remove_databases_failures_skips_non_wrapper_methods` — body unchanged in substance from the ship commit. |
| T-8 | `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` | **holds** | `tests/test_django_patches.py::test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` — still asserts `TransactionTestCase not in _NarrowSimpleTest.__mro__` first. |
| T-9 | `test_unpatched_remove_databases_failures_crashes_on_non_wrapper` — "Temporarily reverts … to **a verbatim copy of Django's upstream body**" | **superseded (mechanism reversed, intent strengthened)** | `tests/test_django_patches.py::test_unpatched_remove_databases_failures_crashes_on_non_wrapper` — now reverts to the **live import-time capture** `_django_patches._original_remove_databases_failures` and first asserts `captured.__func__.__module__ == "django.test.testcases"`. Its docstring names the reason: "A hardcoded copy of the upstream body could not deliver that signal: the copy would keep crashing no matter what the installed Django ships." Changed by **`0d655bde`** (2026-07-13), the same commit that added the tier-3 body pin: `git log --oneline -S'captured.__func__.__module__' -- tests/test_django_patches.py` -> `0d655bde` alone, and the `48f9f65d` blob of this test still carries the hardcoded `"""Verbatim copy of Django 5.2.13's upstream method body."""`. |
| T-10 | `test_apply_no_ops_when_database_failure_symbol_missing` — "Django private-symbol drift does not break package import or app loading." | **REVERSED** | HEAD carries `tests/test_django_patches.py::test_apply_fails_loudly_when_database_failure_symbol_missing`, whose body is `with mock.patch.object(_django_patches, "_DatabaseFailure", None): with pytest.raises(RuntimeError, match="_DatabaseFailure"): _django_patches.apply()`. The plan-era body (`git show d1d19ca2^:tests/test_django_patches.py`) asserted a `caplog` INFO notice and no raise; its companion `test_apply_logs_missing_symbol_notice_only_once` was deleted outright. Module **import** is still protected (the `try/except ImportError` around the symbol survives at `django_strawberry_framework/_django_patches.py #"except ImportError:"`); **app loading** is not — `apply()` now raises. Deliberate, and performed by **`48f9f65d`** (2026-07-11), which is the commit that deleted `logger` / `_missing_symbol_logged`, deleted this test and its log-once companion, and added the two `…fails_loudly…` replacements: `git log --oneline -S'<each of the four test names>' -- tests/test_django_patches.py` returns `48f9f65d` for all four. Its own subject is about the type registry and never mentions this file, so the *reason* is only stated two days later, in `0d655bde`'s body ("shape-passing body drift now refuses to install instead of clobbering a working teardown") — that sentence is `0d655bde`'s, not this commit's. |

**T-11..T-15 — the Phase-4 update's `tests/test/test_wrap.py` line**, quoted as written: "5 regression tests
(install on free slot; decline on `_DatabaseFailure`; private-symbol drift fallback; works on arbitrary
method names; **end-to-end composition** with the unwrap-time patch)".

| # | Planned clause | Verdict | HEAD site |
|---|---|---|---|
| T-11 | "install on free slot" | **holds** | `tests/testing/test_wrap.py::test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure` — asserts `installed is True` and the wrapper is in place. |
| T-12 | "decline on `_DatabaseFailure`" | **holds** | `tests/testing/test_wrap.py::test_safe_wrap_connection_method_declines_when_database_failure_in_place` — asserts `installed is False` **and** that Django's wrapper object is still the attribute. |
| T-13 | "private-symbol drift fallback" | **holds — and note it was NOT flipped** | `tests/testing/test_wrap.py::test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing` — with `_DatabaseFailure` patched to `None`, still asserts `installed is True`. The wrap-time half kept the fail-open posture that the unwrap-time half (T-10) gave up. |
| T-14 | "works on arbitrary method names" | **holds** | `tests/testing/test_wrap.py::test_safe_wrap_connection_method_works_on_arbitrary_method_names` — drives `chunked_cursor`. |
| T-15 | "end-to-end composition with the unwrap-time patch" | **holds** | `tests/testing/test_wrap.py::test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth` — installs a `_DatabaseFailure`, proves the helper declines, then drives `_NarrowTest._remove_databases_failures()` and asserts the sentinel is restored. |

Two wrap tests at HEAD are **beyond** the planned five, both guarding the `TypeError` boundary added by
`7014125a`: `tests/testing/test_wrap.py::test_safe_wrap_connection_method_raises_on_non_callable_wrapper`
and `…::test_safe_wrap_connection_method_keeps_type_error_boundary_for_hostile_repr`.

The 7 wrap tests at HEAD decompose by commit, measured with `grep -c '^def test_'` and by name-set diff
on each blob: **4** at `61973f8d` (the Phase-4 ship) -> **6** at `7014125a` -> **7** at `f7fbead4`. Worth
stating precisely, because the plan's own Phase-4 line calls the file "5 regression tests" while the file
held 4 the day that text was written: the fifth planned clause, **T-13 private-symbol drift fallback**
(`…_installs_when_database_failure_symbol_missing`), landed at `7014125a` alongside the first beyond-plan
test (`…_raises_on_non_callable_wrapper`). The second beyond-plan test
(`…_keeps_type_error_boundary_for_hostile_repr`) is `f7fbead4`'s. So planned-vs-beyond is 5 + 2, but it is
not 5-then-2 in time.

**Path note (P-1).** Both planned locations moved: `django_strawberry_framework/test/_wrap.py` ->
`django_strawberry_framework/testing/_wrap.py` and `tests/test/test_wrap.py` -> `tests/testing/test_wrap.py`,
at `e145ba36` (2026-06-01), because `test` shadows the stdlib `test` package. `git log --diff-filter=D --
django_strawberry_framework/test/_wrap.py` and the matching `--diff-filter=A` on the new path both return
that single commit. The public import path is `django_strawberry_framework.testing`.

#### 3. `TEMP-024.md` `## Required Tests` (3 items)

| # | Required bullet | Verdict | Evidence |
|---|---|---|---|
| R-1 | "`tests/test_django_patches.py` pins the automatic unwrap-time backstop: `AppConfig.ready()` installs the patch on `SimpleTestCase`, `TransactionTestCase` and `TestCase` inherit it, a direct `SimpleTestCase` subclass is covered, a real `_DatabaseFailure` unwraps normally, a plain callable does not crash, the unpatched upstream body still crashes, `apply()` is idempotent and self-healing, **and a missing private `_DatabaseFailure` symbol no-ops with one log notice**." | **holds for 7 of 8 clauses; the 8th is REVERSED** | Clauses 1-7 map to T-3/T-4/T-5/T-8/T-6/T-7/T-9/T-1/T-2 above, all green in the focused run. The `ready()`-installs clause is now pinned deterministically by `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely` rather than only by collection-order luck (its own docstring says the per-module assertions are masked by earlier direct `apply()` calls). Clause 8 is row T-10: no-op-with-log-notice -> `RuntimeError`, and the log-once companion test is gone. |
| R-2 | "`tests/test/test_wrap.py` pins the wrap-time mirror: … installs into a free slot, declines when Django's `_DatabaseFailure` is present, handles arbitrary disallowed method names, composes with the unwrap-time patch, and remains usable if Django moves/removes the private `_DatabaseFailure` symbol." | **holds** (file relocated per P-1) | All five clauses -> T-11..T-15. |
| R-3 | "No root `conftest.py`, base test class, or settings key is acceptable **as the fix**. Consumers get the backstop by installing `django_strawberry_framework`." | **holds as stated; the "settings key" clause needs re-wording for HEAD** | No conftest workaround (DoD 5) and no base test class exists for this purpose. A settings key **does** exist — `conf.py #"APPLY_UPSTREAM_PATCHES_KEY = \"APPLY_UPSTREAM_PATCHES\""` — but it is an **opt-out that defaults to on**, not the delivery mechanism: `django_strawberry_framework/_django_patches.py::apply #"if not upstream_patches_enabled(\"django\"):"` returns early only when a consumer configured it. The consumer still gets the backstop from `INSTALLED_APPS` alone. |

#### 4. The 5 decisions

| # | Decision (quoted head) | Verdict | Evidence | What changed |
|---|---|---|---|---|
| D-1 | "**Where the patch lives.** A new private module (`django_strawberry_framework/_django_patches.py`) rather than inlining in `apps.py`. The patch is ~30 lines of code with a 30-line rationale docstring" | **holds; its stated scale is superseded** | module exists, still underscore-private, still the home of the one Django patch | 91 lines at ship -> **406** at HEAD (`wc -l`), 369 changed lines against the ship copy. The "future Django patches land in the same module" clause held literally: the Django 6.1 body change landed inside this module (`eb2a1764`) rather than as a new one. Its sibling modules `_strawberry_patches.py` / `_cross_web_patches.py` are for **other dependencies** under a different card, so the organizing rule is now one module per *dependency* (`conf.py #"UPSTREAM_PATCH_DEPENDENCIES = frozenset({\"django\", \"strawberry\", \"cross_web\"})"`). |
| D-2 | "**Where the patch is applied.** `DjangoStrawberryFrameworkConfig.ready()`." | **holds** | `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` | Unchanged in substance; the body now dispatches three appliers, imports are function-local so importing `apps` outside Django pulls in no patch module, and `apply()`'s idempotence is `_patch_is_installed()`-based rather than a flag. |
| D-3 | "**Whether to use the original cursor or a sentinel callable in tests.** … **No real Django connection state is mutated for these tests.**" | **reversed in its closing claim (and that claim was never true)** | `tests/test_django_patches.py::test_patched_remove_databases_failures_unwraps_a_real_wrapper #"connection.cursor = wrapper"` — the same assignment is in the ship commit (`git show 300e2811:tests/test_django_patches.py`), so the sentence was already false the day it was written. HEAD widened it: `tests/test_django_patches.py::test_disallowed_methods_read_falls_back_to_the_connection_feature_flag #"for alias in connections:"` writes `connections[alias].features.disallowed_simple_test_case_connection_methods` on **every** alias and `del`etes it in `finally`. | The mechanism half of the decision (sentinel via `_DatabaseFailure(sentinel, …)`, plain `_plain_cursor` for the bug case) **holds** verbatim. Only the "no real state mutated" claim must not be carried into the new spec: real `connections[…]` slots are mutated and restored in `try/finally`. |
| D-4 | "**Whether to ship a `DJANGO_STRAWBERRY_FRAMEWORK` settings escape hatch.** **No** … The patch is strictly defensive — it never makes Django's behaviour worse — so there's no foreseeable reason to opt out." | **REVERSED, in both halves** | (a) Hatch shipped twice over: global bool at `c7cb5f5c` (`git show c7cb5f5c -- django_strawberry_framework/_django_patches.py` adds `if not upstream_patches_enabled(): return`), per-dependency mapping at `a62d6dca`/`0d655bde` (`conf.py::upstream_patches_enabled`, `conf.py #"UPSTREAM_PATCH_DEPENDENCIES"`, `APPLY_UPSTREAM_PATCHES_KEY`). Pinned by `tests/test_django_patches.py::test_apply_no_ops_when_toggle_disabled` and `…::test_apply_no_ops_when_django_dependency_opted_out`. (b) The justification collapsed: `apply()` now **raises `RuntimeError` at app load** on any drift (`django_strawberry_framework/_django_patches.py::_validate_upstream_shape`), and `eb2a1764`'s message records the real-world consequence — "`AppConfig.ready()` raised and the package refused to boot on 6.1". Every drift message names the escape hatch, and `tests/test_django_patches.py::test_django_dependency_opt_out_silences_drifted_pin_abort` pins that coupling end to end. | The hatch is no longer optional polish; it is the documented recovery path for a consumer upgrading Django ahead of the package. |
| D-5 | "**Whether to widen the `databases` allow-list (the previous conftest workaround).** **Rejected.**" | **holds** | `grep -rn "databases *=" --include="*.py" .` (minus `.venv`, migrations, `DATABASES`) returns only `databases = frozenset()` inside synthetic test classes and `@pytest.mark.django_db(databases=[…])` markers — no `"__all__"` widening anywhere | The rejection stands; nothing re-introduced the workaround at any layer. |

#### 5. The 4 risks / open questions

| # | Risk (quoted head) | Closed? | How |
|---|---|---|---|
| K-1 | "**Production cost.** `ready()` runs in production processes too … both are no-op in production runtime … The one-time import cost is small (~10ms). Acceptable." | **partially closed; the assessment is now understated** | The import cost claim still stands (module-level `from django.test.testcases import SimpleTestCase`, function-local import from `ready()`). What changed: `apply()` now runs `inspect.signature` + `inspect.getsource` + a source comparison on **every** call (`django_strawberry_framework/_django_patches.py::_validate_upstream_shape`) before the idempotence check, and it can **raise in a production process at app load**. The rewritten spec must state that the failure mode is fail-closed at startup, not a silent skip. |
| K-2 | "**Class-attribute order under multi-Django-version support.** … When the package upgrades Django, the patch shape may need to evolve. The negative regression test pins the upstream method shape verbatim, so a Django upgrade … will fail the negative test visibly and signal the patch needs updating." | **closed — but by a different mechanism than the risk predicted** | The predicted event happened (Django 6.1, `eb2a1764`). The signal did **not** come from the negative test: it came from `_validate_upstream_shape`'s body pin, which made `ready()` raise. The resolution is the 2-element audited-body set (`_CLASS_ATTRIBUTE_REMOVE_DATABASES_FAILURES_SOURCE`, `_CONNECTION_FEATURE_REMOVE_DATABASES_FAILURES_SOURCE`) plus one read helper `…::_disallowed_connection_methods`. Set size is asserted in-suite: `tests/test_django_patches.py::test_validation_accepts_every_audited_upstream_body_and_refuses_a_third #"assert len(_django_patches._AUDITED_REMOVE_DATABASES_FAILURES_SOURCES) == len(audited)"`. Note the discriminator itself was reversed inside its own series: `hasattr(cls, "_disallowed_connection_methods")` at `eb2a1764` (whose commit message still describes that mechanism) -> the validated body source at `18550f5d`, whose docstring says why the `hasattr` read is *not* equivalent. |
| K-3 | "**`SimpleTestCase` vs `TransactionTestCase`.** … Pinned by `test_patch_is_installed_on_simple_test_case`, `test_patch_is_inherited_by_transaction_test_case`, `test_patch_is_inherited_by_test_case`, and `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`." | **closed** | All four named tests exist at HEAD and pass (T-3, T-4, T-5, T-8). The retarget itself is `7014125a`; the ship commit had it wrong (`git show 300e2811:tests/test_django_patches.py #"test_patch_is_installed_on_transaction_test_case"`). |
| K-4 | "**Future patches in the same module.** `_django_patches.apply()` is the single entry point — additional patches land as more functions in the same module, each with an actual-state check instead of a first-call-wins flag. The module's docstring lists implemented patches" | **partially superseded** | The "actual-state check, not a flag" half holds (`…::_patch_is_installed`, `_PATCH_APPLIED` gone). The "additional patches land in the same module" half holds only within Django: patches for other dependencies got their own modules and their own `apply()`, all dispatched from `ready()`. The docstring's `Currently implemented` list still exists and still names exactly one patch. |

#### 6. `## Out of scope for this plan` (3 items) — did anything get built anyway?

| # | Out-of-scope item | Built anyway? | Evidence |
|---|---|---|---|
| S-1 | "Consumer-facing pytest plugin or `MultiDBTestCase` helper." | **Not by this card. Built later under a different card.** | No pytest plugin and no `MultiDBTestCase` exist. But `django_strawberry_framework/testing/__init__.py::__all__` now exports `TestClient`, `AsyncTestClient`, `GraphQLTestMixin`, `GraphQLTestCase`, `GraphQLTransactionTestCase`, `Response` from `testing/client.py` — which is exactly what the Phase-4 update said the subpackage was pre-staging ("pre-stages where `TestClient` / `GraphQLTestCase` will land at `0.0.12`"). Attributed to spec-043 by the module docstring, not to card 024. |
| S-2 | "Patches for other Django `wontfix` bugs. Track each in its own card." | **No.** | `_django_patches.py` still ships exactly one patch (`Currently implemented` lists one entry; one `def _patched_…` in the module). `_strawberry_patches.py` / `_cross_web_patches.py` patch **other dependencies** and arrived with `c7cb5f5c`, a different card. |
| S-3 | "Upstreaming the patch to Django. Already attempted; closed `wontfix`." | **No.** | Nothing in the tree attempts an upstream submission; the ticket URL is cited as closed in the module docstring, the helper docstring, and the GLOSSARY entry. |

#### 7. The five populations the first pass did not enumerate (folded in from the Worker 3 review)

**Provenance: this subsection is not the first pass's work.** The measured-populations table under
`### Implementation steps` under-enumerated its own inputs: `TEMP-024.md` has **five** `##` sections
(`grep -c '^## ' docs/builder/temp-tests/TEMP-024.md` -> 5) of which exactly one, `## Required Tests`,
was walked, and `PLAN-024.md`'s Phase-4 `**Landed**` list (5 bullets) was not walked at all. The Worker 3
review pass walked all five populations and found that every item holds; that walk is folded in here so
the record is complete in one place, and attributed to the review pass rather than re-derived — a second
unattributed reading of work already done would look like independent confirmation without being it.

| Population | Size | Verdict (review pass) |
|---|---|---|
| `PLAN-024.md` Phase-4 `**Landed**` | 5 bullets | **all hold.** `django_strawberry_framework/testing/{__init__,_wrap}.py` and `tests/testing/{__init__,test_wrap}.py` exist; the signature is `safe_wrap_connection_method(connection: BaseDatabaseWrapper, method_name: str, wrapper: Callable[..., Any]) -> bool` as planned; `docs/GLOSSARY.md` carries both entries **and** the `Public exports` subpackage line, already re-pathed to `django_strawberry_framework.testing`; the `_django_patches.py` docstring points at the helper by its `testing` path. |
| `TEMP-024.md` `## Sources checked` | prose | walked; nothing in it is contradicted at HEAD. |
| `TEMP-024.md` `## Test Placement` | prose | **holds** — coverage is in `tests/`, none in `examples/fakeshop/test_query/`. |
| `TEMP-024.md` `## Efficient Mixed Strategy` | 3 commitments | **all three visible at HEAD**, including the sentinel-over-uninstall conclusion, which survives in the module docstring's `Ecosystem precedent` section as the pattern explicitly *not* available here. |
| `TEMP-024.md` `## Verification Commands` | 3 commands | the third had been run by no pass in this cycle. The review pass ran it: `FAKESHOP_SHARDED=1 uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov -q` -> **36 passed**. Evidence, not a gap — the patch's subject is multi-database teardown and the sharded mode is the only one configuring more than one alias. |

None of the five changes the `no gaps` verdict. What they change is the artifact's standing to state it:
the first pass's population *definition*, not its reading, was the thing that could have hidden a gap.

### Gaps found

**No gaps.** Nothing planned for `DONE-024-0.0.7` is missing from HEAD without having been deliberately
retired. The walk that establishes it: all 9 DoD items accounted for (rows 1-9c), all 15 named tests
located at HEAD (rows T-1..T-15, with T-10 present as an inverted assertion and T-9 present with a
strengthened mechanism), all 3 `TEMP-024.md` required-test bullets satisfied (R-1..R-3), all 5 decisions
still describing HEAD except D-4 (reversed by design) and D-3's closing claim (never true), all 4 risks
closed or explicitly superseded (K-1..K-4), and nothing from the out-of-scope list built under this card
(S-1..S-3). The focused scope runs green: 36 passed, 0 failed, 0 errors.

The one planned behaviour that no longer exists — the missing-symbol **log-once no-op** — is a deliberate
retirement, not a drop. It was performed at **`48f9f65d`** (2026-07-11), which deleted `logger`,
`logger.info` and `_missing_symbol_logged` from the module, deleted both retired tests, and shipped the
replacement assertion in the same file
(`tests/test_django_patches.py::test_apply_fails_loudly_when_database_failure_symbol_missing`). The
*record* of why is not in that commit's message — it names the type registry and never mentions this file
— but in `0d655bde`'s two days later ("fail-loud upstream validation … refuses to install instead of
clobbering a working teardown"). The retirement is therefore evidenced by the diff plus the successor's
statement, not by a self-describing commit; that is a fact the rationale companion should carry rather
than smooth over.

Defects found in passing, both documentation-only (`docs/builder/BUILD.md` `## Severity definitions`:
"comments or docstrings stale or wrong but not load-bearing"):

- **Low — stale cross-module symbol citation.** `django_strawberry_framework/_strawberry_patches.py`
  `#"_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE"` cites a constant that does not exist.
  Measured: `grep -rn "_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE" --include="*.py" --include="*.md" .`
  -> **1 occurrence**, all of it in `_strawberry_patches.py`; the same token in
  `_django_patches.py` -> **0 occurrences**. It was renamed by `eb2a1764` into
  `_CLASS_ATTRIBUTE_…` / `_CONNECTION_FEATURE_…` / `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`, and the
  sibling module's reference was not swept. `_strawberry_patches.py` is **outside this cycle's subject
  surface** — recorded, not fixed (this pass is read-only on all source).
- **Low — two false claims in the shipped `CHANGELOG.md` 0.0.7 entry** (row 9b): "no settings key" and
  "a log-once sentinel suppresses repeated missing-symbol notices". `CHANGELOG.md` is on the build plan's
  baseline-dirty list and this cycle's maintainer scope restriction excludes it, so this is deferred-work
  catalog material, not a repair.
- **Note, not a defect — an ambiguity worth resolving in the rewrite.** `docs/GLOSSARY.md`
  `#"no \`conftest.py\` workaround, no base test class to inherit, no settings key required"` survives
  the D-4 reversal only on the word "required" (no key is *required*; an opt-out key *exists*). The
  CHANGELOG's variant dropped that word and is therefore false. GLOSSARY is out of scope for this cycle.

### Implementation notes

- Ordering choice: every verdict was taken by reading the HEAD body against the planned *sentence*, then
  reaching for git history only to attribute the change to a commit. Name-matching alone would have
  passed T-9 and T-10 (both describe a "the unpatched/missing-symbol case" test that still exists) and
  missed the two inversions.
- The `git show <rev>:<path> > /tmp/dsf-024-*.py` + `diff` form was used for every ship-state comparison.
  No `git stash`, `git checkout`, `git restore`, or `git worktree` was run.
- Counts were measured at the moment they were written, and populations were derived from the shortest
  distinctive token (`^def test_`, `^[0-9]\+\. `, `^- \*\*`) rather than from a descriptive phrase.

### Notes for Worker 3

- Read-only pass; the only diff is this artifact plus a gitignored memory append. There is nothing to
  review in source.
- The one row a re-reviewer should independently re-derive is T-10: it is the single planned contract that
  exists at HEAD with its assertion inverted, and the plan-era body is recoverable with
  `git show d1d19ca2^:tests/test_django_patches.py`.
- Slice 1b owns the floor run. The live suite here resolved Django **6.1**, so only one of the two audited
  body shapes is exercised by the installed dependency; both branches are covered synthetically.

### Notes for Worker 1 (spec reconciliation)

Everything below is a fact the rewritten spec (contract) or the rationale companion (explanations,
rejected alternatives, retired claims) must carry. Spec-side facts are marked **[SPEC]**; rationale-side
**[RATIONALE]**.

**The contract that actually exists at HEAD**

1. **[SPEC]** The package ships two halves of one defense against Django Trac #37064: an **unwrap-time**
   replacement of `django.test.testcases.SimpleTestCase._remove_databases_failures`, applied automatically
   at app load, and a **wrap-time** cooperative helper
   `django_strawberry_framework.testing.safe_wrap_connection_method(connection, method_name, wrapper) -> bool`.
   The patch target is `SimpleTestCase` — the class where Django defines the method — so
   `TransactionTestCase`, `TestCase`, and direct `SimpleTestCase` subclasses are covered by inheritance.
2. **[SPEC]** The public consumer path is `django_strawberry_framework.testing`, **never**
   `django_strawberry_framework.test` (renamed at `e145ba36` because `test` shadows the stdlib package).
   The package's own tests live at `tests/testing/test_wrap.py`.
3. **[SPEC]** `safe_wrap_connection_method` returns `True` when it installed the wrapper, `False` when
   Django's `_DatabaseFailure` was already in place and the wrap was declined, and raises `TypeError`
   when `wrapper` is not callable. It handles the wrap step only — restoration is the consumer's, per the
   worked `setUp`/`tearDown` example in its docstring.
4. **[SPEC]** The **unwrap-time** half — and only that half — is gated by
   `DJANGO_STRAWBERRY_FRAMEWORK["APPLY_UPSTREAM_PATCHES"]`. The setting accepts a `bool` (global) or a
   `Mapping[str, bool]` keyed by `UPSTREAM_PATCH_DEPENDENCIES` = `{"django", "strawberry", "cross_web"}`;
   `{"django": False}` disables this test-only patch while leaving the production request-hardening
   patches installed. Default is on. Any other shape raises `ConfigurationError`.
5. **[SPEC]** `apply()` is **fail-closed**, not fail-open. Before installing it validates three tiers —
   the private `_DatabaseFailure` symbol plus the classmethod descriptor exist; the `(cls)` signature
   holds; the captured original's dedented source is a member of `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`
   — and raises a `RuntimeError` naming the `{"django": False}` escape hatch otherwise. An unreadable
   body (bytecode-only distribution) is treated as drift.
6. **[SPEC]** The audited set has exactly **two** members, spanning the whole supported Django range:
   the `SimpleTestCase._disallowed_connection_methods` class-attribute shape (5.2.16-6.0.x) and the
   per-connection `connection.features.disallowed_simple_test_case_connection_methods` shape (6.1).
   `_disallowed_connection_methods()` discriminates on **the validated body source**, not on
   `hasattr(cls, …)` and not on a version number. Widening the set is an audit, not a version bump.
7. **[SPEC]** `apply()` is idempotent and self-healing through an actual-state check
   (`_patch_is_installed()`), not a first-call-wins flag, and survives an in-process `importlib.reload()`
   by carrying the captured upstream descriptor on the replacement function. Two module-level
   constants name the attributes stamped onto `_patched_remove_databases_failures`:
   `_PATCH_OWNER_ATTRIBUTE` (`"_django_strawberry_framework_patch_owner"`) and
   `_PATCH_ORIGINAL_ATTRIBUTE` (`"_django_strawberry_framework_original"`). A third constant,
   `_PATCH_OWNER` (`"django_strawberry_framework._django_patches"`), is the owner **value** those
   attributes are matched against — not an attribute name — and
   `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor` reads them back.
8. **[SPEC]** `DjangoStrawberryFrameworkConfig.ready()` dispatches three appliers in order —
   `_django_patches`, `_strawberry_patches`, `_cross_web_patches` — behind function-local imports. Only
   the first belongs to this card; the spec should say which of the three it owns and not restate the
   others' inventory.
9. **[SPEC]** No symbol from this work entered `django_strawberry_framework.__all__` — not at the ship
   and not since. The only public export of this work is `safe_wrap_connection_method` from
   `django_strawberry_framework.testing`. **State it without a count.** The root `__all__` held 8 names
   at `300e2811` and holds 37 today; it is the package's whole public surface, it moves every release,
   and a number written into a permanent spec by a card that does not own the list is rot with a
   verification date on it.

**Claims the old planning documents carried that are now FALSE — the rationale companion must record
them as retired, and the spec must not repeat them**

10. **[RATIONALE]** "No `DJANGO_STRAWBERRY_FRAMEWORK` settings escape hatch … there's no foreseeable
    reason to opt out." Reversed twice (`c7cb5f5c`, then `a62d6dca`/`0d655bde`). The underlying
    justification — "strictly defensive; it never makes Django's behaviour worse" — is what actually
    collapsed: `eb2a1764` records `ready()` raising and **the package refusing to boot on Django 6.1**.
    The escape hatch is now the documented recovery path for a consumer upgrading Django ahead of the
    package, and `tests/test_django_patches.py::test_django_dependency_opt_out_silences_drifted_pin_abort`
    pins that coupling.
11. **[RATIONALE]** "A missing private `_DatabaseFailure` symbol no-ops with one log notice" /
    "Django private-symbol drift does not break package import or app loading." Reversed at **`48f9f65d`**
    (2026-07-11) — the commit that deleted `logger`, `logger.info` and `_missing_symbol_logged` and both
    retired tests. Module **import** is still guarded; **`apply()` now raises**. There is no logger in the
    module at HEAD. The log-once companion test was deleted, not renamed. Note for the change record: the
    log-once *sentinel* was itself a `744fd28d` addition made after the plan's last content-bearing write,
    so what the plan promised was the INFO-notice no-op, and the sentinel that made "a single notice" true
    was never in the planned contract at all (see item 23).
12. **[RATIONALE]** "The negative regression test pins the upstream method shape verbatim [by holding a
    hardcoded copy of Django's body]." Reversed at **`0d655bde`** (2026-07-13) — two commits later than
    item 11's reversal, and a separate change: a hardcoded copy would keep crashing no
    matter what the installed Django ships and therefore could never deliver the retirement signal. The
    test now reverts to the live import-time capture and asserts
    `captured.__func__.__module__ == "django.test.testcases"` as its premise. The body-shape pin moved
    into `_validate_upstream_shape`.
13. **[RATIONALE]** "`_patched_remove_databases_failures` — verbatim copy of Django's
    `_remove_databases_failures` body with an `isinstance` guard added. This is exactly the patch Rio
    proposed in the upstream ticket." No longer verbatim: the method-list read is delegated to
    `_disallowed_connection_methods()` so one replacement covers both audited upstream shapes. The
    `isinstance(method, _DatabaseFailure)` guard — the actual ticket proposal — is unchanged.
14. **[RATIONALE]** "No real Django connection state is mutated for these tests." False at HEAD and false
    at the ship commit. The tests assign to `connections["default"].cursor` / `.chunked_cursor` and, in
    the 6.1-shape test, to `connections[alias].features.disallowed_simple_test_case_connection_methods`
    for **every** alias, restoring in `try/finally`. The decision that *does* hold is the sentinel
    technique: `_DatabaseFailure(mock.sentinel.…)` for the happy path, a plain `_plain_cursor` with no
    `.wrapped` for the bug path.
15. **[RATIONALE]** "The patch is ~30 lines of code with a 30-line rationale docstring." 91 lines at ship,
    **406** at HEAD, 369 lines different from the ship copy. The docstring now also carries the
    `django-debug-toolbar` ecosystem precedent (SQL-panel wrap-time `isinstance`, cache-panel PR #1770's
    sentinel-over-uninstall conclusion) and the audited-body widening rule.
16. **[RATIONALE]** "Additional patches land as more functions in the same module." True only within
    Django. The organizing rule at HEAD is **one patch module per third-party dependency**, each with
    its own `apply()` and its own name in `UPSTREAM_PATCH_DEPENDENCIES`.
17. **[RATIONALE]** The card's own first ship was wrong in a way worth recording: `300e2811` installed the
    patch on `TransactionTestCase`, leaving direct `SimpleTestCase` subclasses unprotected, and used a
    `_PATCH_APPLIED` first-call-wins flag that contradicted its own "re-entrant calls are no-ops"
    docstring. Both were corrected at `7014125a`, three days later, along with the guarded
    `_DatabaseFailure` import and the wrap helper's non-callable `TypeError`.
18. **[RATIONALE]** The "repo-root `conftest.py` workaround has been deleted" DoD item was satisfiable
    only vacuously, and the strongest statement of why is a deletion filter, not a token search:
    `git log --all --oneline --diff-filter=D -- conftest.py tests/conftest.py` is **empty** — no
    `conftest.py` has ever been deleted in this repo, on any ref. There was nothing here to delete; the
    workaround lived in the *other* repo (`django-graphene-filters`). The repo-root `conftest.py` that
    exists today was **created** at `57cbd32a` (2026-07-07), six weeks after this card shipped, and is
    the Postgres tier's. Say so, so a future reader does not read it as the workaround's survival.

**Change-record scope — decisions that are Worker 1's, with the evidence attached**

23. **[DECISION — Worker 1's, as spec custodian]** *Where the rationale's change record starts.* The two
    cohorts hand Worker 1 opposite defaults and neither can see the conflict from inside its own angle:
    this artifact treats `7014125a` as the recovered plan's **baseline** (the plan post-dates it, so its
    four changes are not divergences), while 1b catalogues that same commit as four ship **corrections**
    and raises two of them as contract flips (flip 1 `TransactionTestCase` -> `SimpleTestCase`, flip 7
    `_PATCH_APPLIED` -> `_patch_is_installed`) with retired claims. Both readings are internally sound.
    `docs/builder/BUILD.md` `## Spec reconciliation` makes the choice the custodian's, so it is recorded
    here as a decision with evidence, not resolved.

    **The deciding fact, now measured (this pass).** Neither cohort had established the plan document's
    *upper* bound. It is not a window — it is a point:

    ```shell
    git log --format='%h %cI %s' --follow -- docs/PLAN-trac-37064-database-teardown.md
    #   d1d19ca2 2026-05-27T20:16 (deletes it)   df547235 2026-05-27T18:58   974189ad 2026-05-26T19:34
    #   7014125a 2026-05-26T10:21   61973f8d 2026-05-23T18:32   300e2811 2026-05-23T10:42
    git log --format='%h %cI' --follow -- docs/TEMP-trac-37064-test-plan.md
    #   d1d19ca2 …   7014125a 2026-05-26T10:21
    git show "7014125a:docs/PLAN-trac-37064-database-teardown.md" > /tmp/…/plan-7014125a.md
    git show "d1d19ca2^:docs/PLAN-trac-37064-database-teardown.md" > /tmp/…/plan-d1d19ca2.md
    diff /tmp/…/plan-7014125a.md /tmp/…/plan-d1d19ca2.md          # exactly 2 lines
    diff <TEMP at 7014125a> <TEMP at d1d19ca2^>                    # identical
    ```

    - `TEMP-024.md` as recovered is **byte-identical** to its `7014125a` blob.
    - `PLAN-024.md` as recovered differs from its `7014125a` blob by **exactly two lines**, and both are
      mechanical reference rewrites carrying no contract: `AGENTS.md line 20` -> the symbol-qualified
      form (`df547235`, the repo-wide line-NN sweep), and `spec-019-…` -> `SPECS/spec-019-…`
      (`974189ad`). Line 92 sits inside decision D-4's own bullet and line 115 inside DoD item 9's
      version-target sub-bullet; what neither *changes* is a decision's content, a DoD item's content,
      or a test name.
    - Therefore **both recovered documents describe the tree exactly as of `7014125a`**, and the commits
      after it are not described by the plan at any point: `744fd28d` (2026-05-26T15:09, the log-once
      sentinel and its test) and `e82df83d` (2026-05-26T15:27) both land *after* the plan's last
      content-bearing write and the plan was never updated for either. This confirms the window the two
      cohorts guessed at (`7014125a` <= plan < `744fd28d`) and pins it to a single point.
    - **Consequence for the open question the cohorts raised:** the log-once **sentinel** was never part
      of the planned contract. What the plan and `TEMP-024.md` promise is the missing-symbol *no-op with
      one log notice*, which is `7014125a`'s state — where the docstring claimed "a single INFO-level
      notice" while `apply()` called `logger.info` on every call. `744fd28d` added the sentinel to make
      that claim true. So the ship shipped a claim, the plan recorded the claim, and the mechanism came
      afterwards; whichever start point Worker 1 picks, the rationale should not describe the sentinel as
      a planned deliverable.
    - **What each option costs.** (a) Start at `300e2811`: `7014125a` and `744fd28d` become in-release
      corrections carrying their own retired claims — 1b's shape, and the one that survives 1b's measured
      in-tag correction, at the cost of a change record that opens with four days of churn the plan never
      saw. (b) Start at the plan's baseline: flips 1 and 7 must then be stated as "the plan already
      describes the corrected form" rather than omitted, or the record silently loses two contract flips
      that a reader of the *ship* would still hit.

**Deferred-work catalog items (outside this cycle's scope; do not fix here)**

**This list is half of the catalog, not the catalog.** 1a's and 1b's deferred lists are near-disjoint —
they overlap only on `docs/GLOSSARY.md` — so the cycle's catalog is the **union** of the two, and the
final gate must not take either as complete. 1b additionally carries `docs/TREE.md` (two module summary
lines rendered into it) and the in-release-vs-post-ship framing correction; this list additionally
carries items 19-22 below.

19. `django_strawberry_framework/_strawberry_patches.py`
    `#"_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE"` cites a constant renamed away at
    `eb2a1764`. Measured at HEAD `36cd1925`: **1 occurrence** in that file, 0 in the target module. Low.
    **Re-derive before homing — the file is under concurrent edit and the repair appears to have already
    landed in the working tree:** at the time of this pass, `grep -ro '_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE'
    --include='*.py' .` returns **0** occurrences tree-wide while the HEAD blob of `_strawberry_patches.py`
    still returns 1, i.e. the fix is present and uncommitted (the concurrent Slice 3 rename-rot cohort owns
    that file this cycle). Home this item only against a re-measured tree, never against this number.
20. `CHANGELOG.md`'s `## [0.0.7]` -> `### Added` entry for the hardening carries two now-false claims
    ("no settings key"; "a log-once sentinel suppresses repeated missing-symbol notices"). It also landed
    under `### Added` where DoD item 9 asked for `### Fixed`. Low; `CHANGELOG.md` is baseline-dirty.
21. `docs/GLOSSARY.md`'s `Django Trac #37064 hardening` entry says "no settings key **required**" — true
    only on that last word after D-4's reversal, and it omits the fail-closed validation behaviour
    entirely. Worth a wording pass when the GLOSSARY surface is next in scope.
22. The dispatch's "current surface" list named `django_strawberry_framework/testing/_wrap.py` correctly
    but the planning documents' `django_strawberry_framework/test/…` and `tests/test/…` paths are dead;
    any spec text inherited from them must be re-pathed.

---

## Review (Worker 3)

Read-only review pass over Slice 1a's claims. There is no production diff in this slice, so the
subject is whether the artifact's statements are true. Everything below was re-derived in this pass;
commands are quoted so the next reader re-derives rather than accepts
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

### Sample declaration: what I re-derived, and what I accepted unchecked

**Re-derived (reproduced exactly unless a finding says otherwise):**

| Claim | Command | Result |
|---|---|---|
| HEAD test counts 21 / 7 / 8 = 36 | `grep -c '^def test_'` per file; `pytest … --no-cov --collect-only -q` | 21, 7, 8; **36 tests collected** (def-line count and node-id count agree, so no `parametrize` inflation) |
| focused scope green | `uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov -q` | **36 passed** |
| `_django_patches.py` 406 lines, 91 at ship, 369 changed | `wc -l`; `git show 300e2811:… \| wc -l`; `diff … \| grep -c '^[<>]'` | 406, 91, **369** |
| `grep -c logger _django_patches.py` -> 0 | same | **0** |
| `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` -> 1 occurrence, 0 in the target module | `grep -ro <token> --include='*.py' --include='*.md' .` (occurrences, not matching lines) | **1**, in `_strawberry_patches.py`; 0 elsewhere |
| DoD 5 — the conftest workaround never existed here | `git log --all --oneline --diff-filter=D -- conftest.py` -> **empty**; `git log --oneline -- conftest.py` -> **2 commits**, earliest `57cbd32a` (2026-07-07) | verdict **confirmed**, and by stronger evidence than the artifact's `-S` pickaxe: no root `conftest.py` was ever deleted at all, so the item is vacuous for a reason a token search could not have established |
| T-3 / T-4 / T-5 assert identity, not `hasattr` | read `tests/test_django_patches.py` lines 94-130 | all three assert `<cls>._remove_databases_failures.__func__ is _django_patches._patched_remove_databases_failures` — the artifact's name-only "HEAD site" column understates evidence it actually has |
| T-9's premise assertion | read lines 248-292 | `assert captured.__func__.__module__ == "django.test.testcases"` present, mechanism as described |
| `__all__` = 37 at HEAD | `ast` walk of `django_strawberry_framework/__init__.py` | **37** (see Low 2 for what that number does *not* establish) |
| public-surface check | `git diff HEAD -- django_strawberry_framework/__init__.py` | **empty** |
| no source touched by this cohort | `git status --short \| grep '\.py$'` | one entry, `_strawberry_patches.py`, owned by the concurrent repair cohort — not this cycle's |
| [SPEC] note 4's `ConfigurationError` | read `django_strawberry_framework/conf.py::upstream_patches_enabled` | exception name and the two accepted shapes are as stated |
| Every commit hash cited | `git log -1 <hash>`, `git merge-base --is-ancestor <hash> HEAD`, `git merge-base --is-ancestor <hash> 0.0.7` | **two hashes resolve to no ref** — see High/Medium 1 |

**Accepted unchecked (named, so the sample is honest):** the `## Definition of done` = 9 /
decisions = 5 / risks = 4 / out-of-scope = 3 population counts (I read the recovered documents and
the section boundaries agree, but did not re-run the `awk … | grep -c` forms); the wording of the
`KANBAN.md` card body and the `docs/GLOSSARY.md` entry quoted in rows 9a and 9c (both files are
baseline-dirty and out of this cycle's scope); the ruff pass/fail of DoD 7.

### High:

None.

### Medium:

#### M1 — Eight commit citations resolve to no ref and cannot be re-derived from a fresh clone

`8e86e777` (7 occurrences: lines 130, 148, 166, 167, 237, 340, 344) and `e69ff4f9` (1 occurrence:
line 131) are **not ancestors of HEAD and are contained by no branch and no remote**:

```shell
git merge-base --is-ancestor 8e86e777 HEAD   # exit 1
git merge-base --is-ancestor e69ff4f9 HEAD   # exit 1
git branch -a --contains 8e86e777            # empty
git branch -a --contains e69ff4f9            # empty
git show 8e86e777 | git patch-id --stable    # d7618b47… 8e86e777…
git show 0d655bde | git patch-id --stable    # d7618b47… 0d655bde…   <- identical patch-id
git show e69ff4f9 | git patch-id --stable    # ed7790a1… e69ff4f9…
git show 136c5476 | git patch-id --stable    # ed7790a1… 136c5476…   <- identical patch-id
```

They are pre-rewrite duplicates of `0d655bde` and `136c5476`, reachable only in this machine's local
object store. Root cause is measurable: the artifact's stated derivation returns a *different*
population than the one in the table —

```shell
git log --oneline -S'_remove_databases_failures' -- django_strawberry_framework/ tests/        # 10
git log --all --oneline -S'_remove_databases_failures' -- django_strawberry_framework/ tests/  # 23
```

so the table was built from `--all`, and the "deduped of `t3 checkpoint` refs" step swept the
orphaned duplicates *in* rather than out. Worker 1 copies these into a **permanent** rationale
companion; `git show 8e86e777` fails for every future reader.
**Fix:** translate `8e86e777` -> the correct mainline commit per M2, `e69ff4f9` -> `136c5476`, and
re-derive the table from a HEAD-reachable log.

#### M2 — The commit that performed the fail-loud reversal is never named, so three rows are off by one commit even after M1's hash translation

`48f9f65d` (2026-07-11, "Refactor subsystem clear registration and handling") is the commit that
deleted `logger` / `_missing_symbol_logged`, deleted **both** retired tests, and added the
replacement:

```shell
git log --oneline -S'logger' -- django_strawberry_framework/_django_patches.py
#   48f9f65d …   744fd28d …   7014125a …
git log --oneline -S'test_apply_no_ops_when_database_failure_symbol_missing'   -- tests/test_django_patches.py   # 48f9f65d, 7014125a
git log --oneline -S'test_apply_logs_missing_symbol_notice_only_once'          -- tests/test_django_patches.py   # 48f9f65d, 744fd28d
git log --oneline -S'test_apply_fails_loudly_when_database_failure_symbol_missing' -- tests/test_django_patches.py  # 48f9f65d
```

`48f9f65d` appears **0 times** in this artifact. Row T-10 ("Deliberate, per `8e86e777`"), the
`### Gaps found` paragraph ("Its retirement is recorded in `8e86e777`'s message"), and
`### Notes for Worker 1` item 11 ("Reversed at `8e86e777`") all attribute the reversal to
`8e86e777` = `0d655bde` (2026-07-13) — two days and one commit late. T-9's attribution (the
retirement test switched to the live capture) *does* translate correctly to `0d655bde`, so the two
must be split, not translated together.
**Fix:** attribute the symbol-missing reversal and the two test deletions to `48f9f65d`; keep the
body-pin / live-capture change on `0d655bde`.

#### M3 — The commit table is not the population it claims to be

The table is headed "The commits that moved this surface". Measured, the `_django_patches.py`
history alone is 13 commits and this table shares only 8 of them:

```shell
git log --oneline --follow -- django_strawberry_framework/_django_patches.py   # 13
```

Missing from the table: `893465a5`, `744fd28d`, `7cc163db`, `4a25bf42`, `48f9f65d`. Following the
five sibling files raises the surface to 21 reachable commits (independently reproduced — see the
cross-cohort section). The table is also headed "after the ship" while its first five rows are
inside tag `0.0.7`:

```shell
for h in $(git log --format=%h --follow -- django_strawberry_framework/_django_patches.py); do
  git merge-base --is-ancestor $h 0.0.7 && echo "IN-TAG $h"; done
#   IN-TAG 744fd28d 7014125a 61973f8d 893465a5 300e2811   (exactly 5)
```

Worker 1 writes the rationale's change record from this table, so an incomplete population becomes
an incomplete change record with no vocabulary of its own to find it by.

### Low:

#### L1 — "e82df83d … (11th test)" is off by one

```shell
git show "744fd28d:tests/test_django_patches.py" | grep -c '^def test_'   # 11
git show "e82df83d:tests/test_django_patches.py" | grep -c '^def test_'   # 12
```

`e82df83d` adds the **12th** test; it reads as the 11th only because `744fd28d` (10 -> 11) is
absent from the table (M3). The full measured progression is 6 -> 10 -> 11 -> 12 -> 13 -> 17 -> 17
-> 20 -> 21 across `300e2811`, `7014125a`, `744fd28d`, `e82df83d`, `48f9f65d`, `0d655bde`,
`136c5476`, `eb2a1764`, `18550f5d`.

#### L2 — DoD row 8 pairs a correct proof with a number that proves something else, and the number is then written into the spec

The `diff /tmp/dsf-024-init-ship.py /tmp/dsf-024-init-p4.py -> identical` half is the right proof for
the card's claim and it reproduces. The appended "HEAD `__all__` = 37 names" is a different claim
about a different point in time: `__all__` held **8** names at `300e2811` and holds **37** today
(`ast` walk of both blobs). A row reading *holds / unchanged / 37 names* invites the false reading
that the root `__all__` is unchanged at HEAD. `### Notes for Worker 1` item 9 then carries the
number into a permanent spec sentence — "No new symbol entered `django_strawberry_framework.__all__`
(37 names, verified)" — for a list this card does not own and that changes on every release.
**Fix:** keep the claim, drop the count; state "no symbol from this work entered the root `__all__`"
and cite the ship-era diff.

#### L3 — The measured-populations table under-enumerates its own inputs, and two unwalked populations turn out clean

`TEMP-024.md` has five `##` sections; exactly one (`## Required Tests`) is an enumerated population.
`## Sources checked`, `## Test Placement`, `## Efficient Mixed Strategy`, and
`## Verification Commands` were never walked, and neither was `PLAN-024.md`'s Phase-4 `**Landed**`
list (5 bullets). I walked all of them in this pass, working from the planned list inward:

- Phase-4 `**Landed**` (5 bullets) — all hold. `django_strawberry_framework/testing/{__init__,_wrap}.py`
  and `tests/testing/{__init__,test_wrap}.py` exist; the signature is
  `safe_wrap_connection_method(connection: BaseDatabaseWrapper, method_name: str, wrapper: Callable[..., Any]) -> bool`
  as planned; `docs/GLOSSARY.md` carries both entries **and** the `Public exports` subpackage line,
  already re-pathed to `django_strawberry_framework.testing` (GLOSSARY.md line 69); the
  `_django_patches.py` docstring points at the helper by its `testing` path.
- `## Test Placement` — holds; coverage is in `tests/`, none in `examples/fakeshop/test_query/`.
- `## Efficient Mixed Strategy` — all three commitments are visible at HEAD, including the
  sentinel-over-uninstall conclusion, which survives in the module docstring's `Ecosystem precedent`
  section as the pattern explicitly *not* available here.
- `## Verification Commands` — the third command was never run by either cohort. I ran it:
  `FAKESHOP_SHARDED=1 uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov -q` -> **36 passed**.
  This closes as evidence, not as a gap: the patch's own subject is multi-database teardown, and the
  only mode in which more than one alias is configured had never been executed against it in this
  cycle.

Nothing in these four populations changes the `no gaps` verdict. The finding is that the artifact's
population definition, not its reading, was the thing that could have hidden one.

#### L4 — Deferred item 19's subject is under live concurrent edit

`django_strawberry_framework/_strawberry_patches.py` is `M` in the working tree (`git status --short`),
owned this cycle by a concurrent repair cohort. The 1-occurrence measurement is true of the HEAD blob
but the catalog entry may be closed or moved before Slice 2 reads it. Mark the item "measured at HEAD
`36cd1925`; file under concurrent edit — re-derive before homing."

### Cross-cohort check against Slice 1b

The two cohorts were produced independently and never read each other. Where they touch the same
fact:

- **Agree — the load-bearing verdict.** Both return no code gap. I re-derived it independently from
  the planned list inward (L3 above plus the DoD/test/decision rows I sampled) and **concur**:
  nothing planned for `DONE-024-0.0.7` is absent from HEAD without a deliberate, tested retirement.
- **Disagree — `e82df83d`'s test number.** 1a: "11th test". 1b §5: "11 -> 12 tests". Measured, **1b is
  right** (L1).
- **Disagree — the commit population.** 1a's 13-row table vs 1b's measured 21-commit surface / 13-commit
  file history. The two lists share 8 members; 1a's contains 2 unreachable hashes, 1b's contains none.
  I reproduced every one of 1b's six `--follow` counts (13 / 8 / 8 / 13 / 7 / 9), its 23-commit union,
  and its 21-commit surface. **1b is right.**
- **Classification conflict neither cohort can see.** 1a treats `7014125a` as the recovered plan's
  *baseline* ("they are its updated form, so it is the baseline, not a divergence"), which makes its
  four changes invisible to the change record. 1b catalogues the same commit as four ship
  **corrections** and raises two of them as contract flips (flip 1 `TransactionTestCase` ->
  `SimpleTestCase`, flip 7 `_PATCH_APPLIED` -> `_patch_is_installed`) with retired claims the
  rationale must carry. Both readings are individually sound. Worker 1 must decide whether the
  rationale's change record starts at `300e2811` or at the plan's baseline — the two artifacts hand
  it opposite defaults. Note also that 1a establishes the plan's *lower* bound and neither cohort
  establishes its *upper* bound: `PLAN-024.md` lists 10 tests and the file held 11 by `744fd28d`, so
  the recovered plan is a snapshot in the window `7014125a` <= plan < `744fd28d`. That window is what
  decides whether the log-once sentinel was ever part of the planned contract at all.
- **Deferred catalogs are near-disjoint.** 1a: `_strawberry_patches.py` citation rot, `CHANGELOG.md`,
  `docs/GLOSSARY.md`. 1b: `docs/GLOSSARY.md`, `docs/TREE.md`, and the in-release-vs-post-ship framing
  correction. Only GLOSSARY overlaps. Worker 1 needs the union, not either list.

### DRY findings

Not applicable in the usual sense — the pass adds no code and introduces no abstraction, so there is
no existence challenge to raise. One documentation-level near-copy worth naming: rows 9b, the
`### Gaps found` bullets, and `### Notes for Worker 1` items 19-21 state the same three deferred
items three times in three wordings, and the M2 mis-attribution is duplicated across all three
statements of it. Single-source them so a correction lands once.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> empty. `__all__` and the re-export list
are unchanged; no export from this work entered the package root (`safe_wrap_connection_method` is
reachable only at `django_strawberry_framework.testing`).

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. (Its *findings* about `CHANGELOG.md` are
deferred-catalog material and correctly not fixed here — the file is baseline-dirty and outside this
cycle's maintainer scope restriction.)

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Its only write is this
artifact.

### Failability proofs

None owed and none recorded: the slice introduces no boundary, guard, gate, or rejection path. My
independent re-run set is therefore **empty**, which `worker-3.md` makes legal only in exactly this
case ("An empty re-run set is legal only when the diff introduces no boundary that meets the floor").
No source file was mutated in this pass; the transient-mutation carve-out was not exercised.

### Hot-path budget

Not applicable; the build plan declares no hot path, and the review found nothing that contradicts
that declaration (`apply()` runs once per `ready()`; the `inspect.getsource` cost 1a flags in K-1 is
app-load, not per-request).

### Static helper

`scripts/review_inspect.py` **not run**, and this is a recorded skip: the pass reviews Markdown
claims and git history rather than new logic, the build plan's pre-flight already ran it on
`_django_patches.py`, and no repeated-literal or import-boundary evidence was needed for any finding.

### Temp test verification

- `docs/builder/temp-tests/024-review/probe_discriminator.py` (gitignored) — executed under both
  interpreters to re-derive 1b's discriminator table independently of 1b's own probe.
- Disposition: **not promoted.** `tests/test_django_patches.py::test_disallowed_methods_read_prefers_the_class_attribute_shape`
  and `…::test_disallowed_methods_read_falls_back_to_the_connection_feature_flag` already pin both
  branches synthetically; the probe's only added value is executing them against a real interpreter
  at each end of the supported range, which is the floor run's job, not a permanent test's.

### What looks solid

- **The method, not just the result.** Reading each planned *sentence* against the HEAD body instead
  of matching names is what caught T-9 and T-10, and the artifact says so. Both inversions survive a
  name-based sweep; I re-read both bodies and confirm the verdicts.
- **T-10 held up to independent re-derivation.** `git show d1d19ca2^:tests/test_django_patches.py`
  carries the `caplog` INFO assertion and the log-once companion; HEAD carries
  `pytest.raises(RuntimeError, match="_DatabaseFailure")`. The reversal is real and correctly graded
  as deliberate rather than as a drop.
- **DoD 5 is right for a better reason than stated** — no root `conftest.py` was ever deleted in this
  repo at all, which is stronger than the `-S` token evidence the artifact gives.
- **D-3's "no real Django connection state is mutated" catch.** Establishing that the claim was false
  *at the ship commit* rather than only at HEAD is the difference between a divergence and a
  never-true claim, and it is exactly the distinction the rationale companion exists to record.
- **Scoping DoD 7's ruff claim to the 8 subject files** rather than asserting a repo-wide `.` pass a
  read-only cohort cannot attest to, in a tree dirty with concurrent work.

### Notes for Worker 1 (spec reconciliation)

- **Escalated — change-record starting point.** The 1a/1b classification conflict above. Resolution
  paths: (a) the rationale's change record starts at `300e2811` and treats `7014125a` / `744fd28d`
  as in-release corrections with their own retired claims (1b's shape, and the one that survives
  1b's measured in-tag correction); or (b) it starts at the recovered plan's baseline and records
  only post-baseline movement, in which case flips 1 and 7 must be stated as "the plan already
  describes the corrected form" rather than omitted. Pick one explicitly; the two artifacts default
  opposite ways.
- **Escalated — the plan's upper bound.** Establish the `7014125a` <= `PLAN-024.md` < `744fd28d`
  window (or refute it) before writing "the planned contract was N tests". Whether the log-once
  sentinel was ever *planned* turns on it.
- Do not carry the `37 names` count into the spec (L2). Do not carry any raw `path:NN` line number
  out of either artifact into the spec or rationale — `AGENTS.md` restricts those to per-cycle
  `bld-*.md` scratchpads, and 1b's TREE.md escalation is written in that form.
- The deferred-work catalog for this cycle is the **union** of both artifacts' lists, plus 1a's L4
  caveat that `_strawberry_patches.py` is under concurrent edit.

### Review outcome

`revision-needed`.

The cohort's load-bearing verdict — **no code gap** — is correct and I independently re-derived it,
including from two populations the artifact never enumerated. What fails the gate is the change
record built alongside it: three Medium findings (M1 dead citations, M2 wrong-commit attribution,
M3 incomplete population) all corrupt facts Worker 1 is instructed to copy verbatim into a permanent
rationale companion, and all three are mechanically fixable by Worker 2 without spec context, so the
`review-accepted`-with-escalation route in `worker-3.md` does not apply. The re-pass is scoped to
citations, attributions, and counts; the walk itself does not need redoing.

---

## Build report (Worker 2, pass 2)

Apply-changes pass over the Worker 3 review. **Read-only on all source**: no `.py` file, no spec file, no
build-plan file, no baseline-dirty file was touched. The only writes are this artifact and the gitignored
memory file. The review's load-bearing verdicts — **no code gap** here, **floor pass** in 1b — were not
re-opened; every fix below is to the change record.

### Files touched

- `docs/builder/bld-slice-1a-024-planned_vs_head.md` — this artifact (body corrected above; this report
  appended).
- `docs/builder/worker-memory/worker-2-024.md` — one appended entry (gitignored, append-only).

`git status --short` after the pass shows no `.py` entry attributable to this pass; the single `M
django_strawberry_framework/_strawberry_patches.py` belongs to the concurrent Slice 3 cohort and was not
touched (see item 19).

### Tests added or updated

None (read-only pass).

### The reachability sweep, so the next reader does not redo it

Every 8-hex token in **both** artifacts was extracted and resolved, not just the two the review named:

```shell
cat docs/builder/bld-slice-1a-024-planned_vs_head.md \
    docs/builder/bld-slice-1b-024-divergence_and_floor.md \
  | grep -oE '\b[0-9a-f]{8}\b' | sort -u          # 34 distinct tokens (measured after this pass's edits)
# per token:
git cat-file -e <t>^{commit}                       # is it a commit at all?
git merge-base --is-ancestor <t> HEAD && echo reachable || echo ORPHAN
```

Result: **32 are commits, and 30 of those are HEAD-reachable. Exactly two are orphans** — `8e86e777` and
`e69ff4f9` — confirming the review's finding and establishing that no third one hides behind it. The
remaining 2 tokens (`d7618b47`, `ed7790a1`) are not commit ids at all: they are patch-ids quoted inside the
review's own M1 evidence block. (`e2765ff3` from `git rev-parse 0.0.7` *is* resolvable — it is the tag
object, and `e2765ff3^{commit}` peels to `72f6cd9b`, which is why it counts as reachable rather than as a
non-commit. Worth naming: a token that is not a commit id and a token that is a tag id both look like a
hash, and only the peel distinguishes them.)

Equivalence proved by patch-id, not by message or date:

```shell
git show 8e86e777 | git patch-id --stable   # d7618b47ea05… 8e86e777c617…
git show 0d655bde | git patch-id --stable   # d7618b47ea05… 0d655bde93c9…   same patch-id
git show e69ff4f9 | git patch-id --stable   # ed7790a155e8… e69ff4f905bc…
git show 136c5476 | git patch-id --stable   # ed7790a155e8… 136c54765bb8…   same patch-id
git branch -a --contains 8e86e777           # empty
git branch -a --contains e69ff4f9           # empty
```

Both orphans are pre-rewrite duplicates reachable only in this machine's local object store; a fresh clone
resolves neither. Every replacement (`0d655bde`, `136c5476`, `48f9f65d`) was proved reachable by the same
`--is-ancestor` check before it was written.

### Findings addressed

- **M1 — eight dead citations.** All eight replaced, but **not** by blanket substitution (see M2). Body
  occurrences of `8e86e777`: 7, now 0. Body occurrences of `e69ff4f9`: 1, now 0. Counted with
  `awk 'NR<the review section's first line> && /<token>/'` before and after; the remaining occurrences of both tokens in this
  file are inside the Worker 3 review section, which is the reviewer's record of what was found and is
  not edited.
  **The derivation was fixed, not just its output.** The `--all` log the table was built from returns 23
  commits where the HEAD-reachable form returns 10, and the "dedupe" step over the larger population kept
  orphaned duplicates rather than dropping them. The rebuilt table states the derivation, states why
  `--all` is the wrong instrument in a repo whose history gets rewritten by concurrent sessions, and is
  built from the `--follow` union with a per-member `--is-ancestor` proof.
- **M2 — the fail-loud reversal attributed to the wrong commit.** Split, not translated. `48f9f65d`
  (2026-07-11) now owns the symbol-missing reversal in row T-10, `### Gaps found`, `### Notes for Worker 1`
  item 11, and the DoD 9b sentence; `0d655bde` (2026-07-13) keeps the body pin and the retirement test's
  switch to the live capture in row T-9 and item 12. Re-derived independently of the review:
  `git log --oneline -S'<name>' -- tests/test_django_patches.py` returns `48f9f65d` for all four test
  names (both deletions, both replacements) and `git log --oneline -S'captured.__func__.__module__'`
  returns `0d655bde` alone; the `48f9f65d` blob of the retirement test still carries
  `"""Verbatim copy of Django 5.2.13's upstream method body."""`, which is the direct proof the two are
  different changes. `48f9f65d` appeared 0 times in this artifact and now appears in five places.
  One thing the review did not say and the record now does: `48f9f65d`'s subject is about the type
  registry and never mentions this file, so the *reason* for the reversal exists only in `0d655bde`'s
  body. Attributing the quote and the change to one commit is what produced the original error.
- **M3 — the table is not the population it claims.** Replaced. The table is now the **21 reachable
  commits** that touch the six surface files (union of `--follow`, 23, minus `b972cd84` / `dfa035b4`
  which are 2026-05-21 AppConfig work predating the 2026-05-23 ship), each row carrying an explicit
  `in 0.0.7` / `post-tag` column measured with `git merge-base --is-ancestor <sha> 0.0.7`. Six rows are
  in-tag, so the old "after the ship" heading is gone. The five commits the review named as missing
  (`893465a5`, `744fd28d`, `7cc163db`, `4a25bf42`, `48f9f65d`) are present, as are six more the review
  did not enumerate (`52d97ec0`, `b8a8a6e0`, `7c2a63ed`, `5a74d803`, `f7fbead4`, `36cd1925`).
- **DoD 5 — the stronger reason.** Row 5 now states it: no `conftest.py` was ever deleted in this repo on
  any ref (`--diff-filter=D` over both paths is empty), and the only repo-root `conftest.py` that has ever
  existed was *created* six weeks after this card shipped. Item 18 carries the same correction.
- **DoD 8 — "unchanged" carrying today's number.** Verdict and number both corrected. The row now says
  what the card owns ("unchanged *by this card*"), records the measured 8-at-`300e2811` / 37-at-HEAD
  movement as belonging to other cards, and item 9 instructs the spec to carry the claim **without a
  count**. AST walk of both blobs, not `grep`, since `__all__` spans many lines.
- **L1 — `e82df83d` is the 12th test, not the 11th.** Corrected in the table row, and the full progression
  is now stated per commit.
- **L2, L3, L4** — L2 is the DoD 8 fix above; L3 is folded in as walk section 7, explicitly attributed to
  the review pass; L4 is carried into item 19 with the concurrent-edit caveat and a re-measurement.
- **Cross-cohort classification conflict** — recorded as item 23, framed as **Worker 1's decision**, with
  both readings, what each costs, and the missing deciding fact now measured (below). Not resolved here:
  `docs/builder/BUILD.md` `## Spec reconciliation` makes the spec Worker 1's alone.
- **The catalog is a union** — stated above the deferred list here, and in 1b's notes.

### The plan's upper bound, measured (the fact neither cohort had)

Both cohorts flagged that the conflict turns on when the recovered plan was written, and neither measured
it. It is not a window; it is a point. `TEMP-024.md` as recovered is byte-identical to its `7014125a`
blob, and `PLAN-024.md` as recovered differs from its `7014125a` blob by exactly two lines, both
mechanical reference rewrites (`974189ad`, `df547235`) carrying no contract. So both documents describe
the tree as of `7014125a` and describe nothing after it. Full commands and the consequence — the log-once
**sentinel** (`744fd28d`) was never in the planned contract, only the INFO-notice no-op it was later built
to make true — are in item 23.

### Failability proofs

None; this pass introduced no boundary. It is read-only on all source and edits Markdown only.

### Hot-path budget

Not applicable; the build plan declares no hot path, and this pass changes no code.

### Floor verification

Not owned by this pass, and not re-run. The plan assigns the floor run to Slice 1b, the Worker 3 review
re-executed it in full and accepted it, and the dispatch for this pass declares floor scope **none**. The
venv at `/tmp/dsf-floor-024` was left untouched; no `uv pip install` was issued in this pass, into it or
into the shared `.venv`.

### Validation run

- `uv run ruff format <files this pass touched>` — **not run**: this pass touched no `.py` file. Ruff's
  write mode is not run on Markdown.
- `uv run ruff check --fix <the same files>` — **not run**, same reason.
- `git status --short` after the pass — the only entries attributable to it are this artifact and
  `docs/builder/bld-slice-1b-024-divergence_and_floor.md` (both already tracked as this cycle's artifacts).
  Everything else present is the build plan's baseline-dirty set, the concurrent Slice 3 cohort's
  `_strawberry_patches.py`, or the build plan itself. Nothing reverted, nothing tidied.
- No `pytest` run in this pass, focused or otherwise: no assertion changed and none of the corrections is
  a behavioural claim. The green focused scope (36 passed) and the floor run stand on the earlier passes'
  records, both re-executed by the reviewer.

### Implementation notes

- **Every number in the corrected text was re-measured in this pass, including numbers the first pass got
  right.** `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` makes that
  unavoidable: which inherited numbers were measured is not visible from reading them. Three of the
  re-measured ones moved (below), and none of the three announced itself.
- Populations were derived from the shortest distinctive token and counted as **occurrences**, not
  matching lines: `grep -oE '\b[0-9a-f]{8}\b'` for hashes, `grep -c '^def test_'` on extracted blobs for
  test counts, an AST walk for `__all__` (a multi-line list `grep -c` would count wrong).
- Every historical read is `git show <rev>:<path>` into `/tmp/dsf-024-fix/` (outside the repo) followed by
  `diff`. No `git stash`, `git checkout`, `git restore`, or `git worktree` was run at any point.
- The rebuilt table keeps the descriptions the first pass measured where they survived re-measurement, and
  every new row's one-line description is grounded in that commit's own `--stat` over the six surface
  files plus a blob-level test count, not in the sibling artifact's prose.

### Notes for Worker 3

- The diff for this pass is two Markdown files. There is nothing to review in source, and the review's own
  M1/M2/M3 evidence blocks were deliberately left untouched — a reviewer's findings are the record of what
  was found.
- The three highest-value things to re-derive: the 21-commit population (the `--follow` union minus the two
  2026-05-21 commits), the `48f9f65d`-vs-`0d655bde` split (four `-S` searches on test names plus the
  `48f9f65d` blob of the retirement test), and the plan's upper bound (the two-line diff between the
  recovered `PLAN-024.md` and its `7014125a` blob).
- One disagreement with the review is recorded under `### Notes for Worker 1` item 24 rather than acted on
  silently; it concerns L1's stated progression, not L1's finding, which is correct.

### Notes for Worker 1 (spec reconciliation)

All of this pass's spec-facing output lands in the body's `### Notes for Worker 1 (spec reconciliation)`
above, which is the section Worker 1 reads. Two items are new in this pass and are named here so they are
not missed:

- **Item 23** — the change-record starting point, presented as a decision that is yours, with both
  readings, the cost of each, and the plan's upper bound now measured to a point rather than a window.
- **Item 24 (below)** — a correction to a number stated inside the Worker 3 review section, which cannot
  be edited there.

24. **[RECORD — disagreement with the review, stated rather than silently declined]** The review's L1
    gives the full test progression as "6 -> 10 -> 11 -> 12 -> 13 -> 17 -> 17 -> 20 -> 21 across
    `300e2811`, `7014125a`, `744fd28d`, `e82df83d`, `48f9f65d`, `0d655bde`, `136c5476`, `eb2a1764`,
    `18550f5d`". L1's **finding** is correct (`e82df83d` adds the 12th test, not the 11th) and is applied.
    Its **progression** attributes the 12 -> 13 step to `48f9f65d`, which does not reproduce:

    ```shell
    git show "e82df83d:tests/test_django_patches.py" | grep -c '^def test_'   # 12
    git show "c7cb5f5c:tests/test_django_patches.py" | grep -c '^def test_'   # 13
    git show "48f9f65d:tests/test_django_patches.py" | grep -c '^def test_'   # 13
    diff <names at e82df83d> <names at c7cb5f5c>   # + test_apply_no_ops_when_toggle_disabled
    diff <names at c7cb5f5c> <names at 48f9f65d>   # -2 (no_ops_when_symbol_missing,
                                                   #     logs_missing_symbol_notice_only_once)
                                                   # +2 (both fails_loudly_…)
    ```

    `c7cb5f5c` (the settings gate) takes 12 -> 13; `48f9f65d` is 13 -> 13, deleting two rows and adding
    two. The corrected progression is in the body under the rebuilt table. This matters to the rationale
    for the same reason M2 does: a net-zero commit that swaps two tests for two others is exactly the
    shape a count-only record cannot see, and reading `48f9f65d` as "+1 test" hides that it is the commit
    where the graceful-degradation contract was retired.

---

## Review (Worker 3, pass 2)

Re-review of the apply-changes pass, not a fresh review. The two load-bearing verdicts — **no code
gap** here and **floor pass** in 1b — were reproduced by the prior pass and are not re-opened; the
floor venv was not re-run and the planned-contract walk was not redone. The subject is narrow: did
the fixes land, are the *new* numbers true, and did the repair introduce anything.

**Tree state at this pass.** `HEAD` is now **`f466863a`**, not the `36cd1925` both artifacts record as
their audit HEAD. The single intervening commit (`docs(specs): extract the spec-023 rationale …`) is a
concurrent session's and touches **none** of the six surface files:

```shell
git log --oneline 36cd1925..HEAD                      # f466863a  (one commit)
git log --oneline 36cd1925..HEAD -- django_strawberry_framework/_django_patches.py \
    django_strawberry_framework/testing/_wrap.py django_strawberry_framework/apps.py \
    tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py   # empty
```

Every count and every citation in both artifacts therefore still holds against the *current* HEAD, and
`36cd1925` remains a HEAD ancestor. Recorded so Slice 2 does not read the moved HEAD as drift.

### Sample declaration: what I re-derived, and what I accepted unchecked

**Re-derived in this pass (all reproduce exactly unless a finding says otherwise):**

| Claim | Command | Result |
|---|---|---|
| the whole 8-hex sweep | `cat <both artifacts> \| grep -oE '\b[0-9a-f]{8}\b' \| sort -u`, then per token `git cat-file -t`, `git cat-file -e <t>^{commit}`, `git merge-base --is-ancestor <t> HEAD` | **34 distinct; 32 peel to a commit; 30 HEAD-reachable; exactly 2 orphans** (`8e86e777`, `e69ff4f9`) — the builder's numbers reproduce cell for cell |
| `d7618b47` / `ed7790a1` really are patch-ids | `git cat-file -t <t>` | **object missing** in both cases — not commits, not tags, not any object; consistent with patch-ids quoted inside M1's evidence block |
| `e2765ff3` really is the tag peeling to `72f6cd9b` | `git cat-file -t e2765ff3`; `git rev-parse 0.0.7`; `git rev-parse '0.0.7^{commit}'` | **`tag`**; `e2765ff31f63…`; **`72f6cd9be9d7…`** |
| the orphans are gone from both bodies | `grep -n -o -E '8e86e777\|e69ff4f9'` on each file, line numbers mapped against the section boundaries | 1a: all occurrences fall in the Worker 3 review section (lines 592-638) or in the pass-2 report's own description of the sweep (891-917). 1b: review section (1128) and pass-2 report (1330). **0 in either body.** |
| M2 half 1 — `48f9f65d` owns the symbol-missing reversal | `git show 48f9f65d -- …/_django_patches.py \| grep -E '^[-+].*(logger\|_missing_symbol_logged)'`; `git log --oneline -S'<name>' -- tests/test_django_patches.py` for all four test names | `-from . import logger`, `-_missing_symbol_logged = False`, `-logger.info(`, `+_validate_upstream_shape()` all in `48f9f65d`; all four test names return `48f9f65d` (the two deletions additionally return `7014125a` / `744fd28d`, their births) |
| M2 half 2 — `0d655bde` owns the body pin + live capture | `git log --oneline -S'captured.__func__.__module__' -- tests/test_django_patches.py`; `git show 48f9f65d:tests/test_django_patches.py \| grep 'Verbatim copy'` | **`0d655bde` alone**; the `48f9f65d` blob still carries `"""Verbatim copy of Django 5.2.13's upstream method body."""` — the two are provably different changes |
| no row got the wrong half | read T-9, T-10, `### Gaps found`, notes 11 and 12, DoD 9b | T-10 / gaps / note 11 / 9b -> `48f9f65d`; T-9 / note 12 -> `0d655bde`. **Correct in all six places.** |
| `__all__` 8 at ship, 37 at HEAD | `ast` walk of `git show 300e2811:…/__init__.py` and of the HEAD file; filtered for `wrap`/`patch`/`testing` | **8**, **37**, filter -> **`[]`** |
| `e82df83d` adds the 12th test | `git show ${h}:tests/test_django_patches.py \| grep -c '^def test_'` per commit; name-set `diff` | 11 at `744fd28d` -> **12** at `e82df83d`, the added name being `test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict` |
| the full corrected progression | same, all 13 commits | **6, 6, 6, 10, 11, 12, 13, 13, 17, 17, 20, 21, 21** across `300e2811`, `893465a5`, `61973f8d`, `7014125a`, `744fd28d`, `e82df83d`, `c7cb5f5c`, `48f9f65d`, `0d655bde`, `136c5476`, `eb2a1764`, `18550f5d`, `36cd1925` — the rebuilt table's line reproduces exactly |
| entry 13 is 13 -> 13, and `c7cb5f5c` owns 12 -> 13 | name-set `diff` of the three blobs | `e82df83d`->`c7cb5f5c`: **+`test_apply_no_ops_when_toggle_disabled`**. `c7cb5f5c`->`48f9f65d`: **-2 / +2**, exactly the four names. **The builder's new finding is correct.** |
| the 21-commit surface and its 6/15 split | `--follow` union over the six files; `merge-base --is-ancestor <h> 0.0.7` per member | union **23**, all HEAD-reachable, **8** in-tag; minus `b972cd84` / `dfa035b4` (2026-05-21, pre-ship) = **21 surface, 6 in-tag, 15 post-tag** |
| the recovered documents' population counts (accepted unchecked by the prior pass) | the artifact's own `awk … \| grep -c` forms, re-run | **9 / 10 / 3 / 5 / 4 / 3**, `TEMP-024.md` `^## ` -> **5**, Phase-4 `**Landed**` -> **5 bullets**. All seven reproduce |
| `_django_patches.py` 406 lines, spec stub 1,618 bytes, `grep -c logger` -> 0 | `wc -l`, `wc -c`, `grep -c` | **406**, **1618**, **0** |
| HEAD blob is `18550f5d`'s | `git show 18550f5d:… \| diff - <working file>` | **identical** |
| public-surface check | `git diff HEAD -- django_strawberry_framework/__init__.py` | **empty** |
| symbol citations resolve | AST-free token sweep: every backticked identifier in both bodies, checked against the set of every identifier in every non-`docs` `.py` in the tree | 9 non-resolving tokens in 1a, 5 in 1b — **all but one are deliberately-cited retired symbols** (`_PATCH_APPLIED`, `_missing_symbol_logged`, the two deleted test names, `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`) or non-symbols (a GLOSSARY anchor, a settings module, `MultiDBTestCase` cited as absent). The exception is **M1 below** |

**Accepted unchecked (named, so the sample is honest):** the prose classification of each catalog entry
as `correction` / `serves-later-work` / cosmetic; the `docs/TREE.md` line numbers in 1b's escalation; the
commit-message quotations in entries 12 and 18; the ruff pass/fail of DoD 7; the `KANBAN.md` and
`docs/GLOSSARY.md` wording quoted in rows 9a / 9c and the deferred items (both files are baseline-dirty
and outside this cycle's scope).

### High:

None.

### Medium:

#### M1 — `_PATCH_ORIGINAL` is a symbol that has never existed, and it is written into a **[SPEC]** note Worker 1 copies into the permanent spec

Two sites, both in the body:

- line 173, the `18550f5d` table row: "Reload-safe capture (`_PATCH_OWNER`/`_PATCH_ORIGINAL` attributes)"
- line 405, `### Notes for Worker 1` item 7, marked **[SPEC]**: "carrying the captured upstream descriptor
  on the replacement function (`_PATCH_OWNER` / `_PATCH_ORIGINAL` attributes)"

Measured:

```shell
grep -rno '\b_PATCH_ORIGINAL\b'           --include='*.py' .   # 0 occurrences, tree-wide
grep -rno '\b_PATCH_ORIGINAL_ATTRIBUTE\b' --include='*.py' .   # 9
grep -rno '\b_PATCH_OWNER\b'              --include='*.py' .   # 9
git log --all --oneline -S'_PATCH_ORIGINAL' -- django_strawberry_framework/   # 18550f5d (+ its orphan twin)
git show 18550f5d -- django_strawberry_framework/_django_patches.py | grep -E '^\+.*_PATCH'
#   +_PATCH_OWNER_ATTRIBUTE = "_django_strawberry_framework_patch_owner"
#   +_PATCH_ORIGINAL_ATTRIBUTE = "_django_strawberry_framework_original"
#   +_PATCH_OWNER = "django_strawberry_framework._django_patches"
```

The `-S` hit is the substring inside `_PATCH_ORIGINAL_ATTRIBUTE`; as a whole token `_PATCH_ORIGINAL` has
**0 occurrences at every revision, on any ref**. The sentence is wrong twice over: the two attribute-name
constants are `_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE`, and `_PATCH_OWNER` — which does
exist — is not an attribute at all but the owner *value* those attributes are compared against
(`django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor
#"if getattr(function, _PATCH_OWNER_ATTRIBUTE, None) == _PATCH_OWNER:"`).

**Why this is Medium and not a nitpick.** It is a symbol citation that resolves to nothing, in the one
section the build plan instructs Worker 1 to write the contract from, destined for an archived spec
governed by `AGENTS.md`'s symbol-path rule. It is the same defect class this cycle's **Slice 3 exists to
repair** (`_strawberry_patches.py`'s citation of a constant renamed away at `eb2a1764`, which shipped and
survived four months because no gate resolves a symbol citation) and the same class the Slice 3 review
escalated to the maintainer. Accepting one into a *fresh* permanent spec while the same cycle repairs
another is the uneven application of a standard that 1b's own reviewer named as the reason a defect
survives a review. The sibling artifact gets all four names right at 1b lines 397-399, so this is also a
live cross-cohort contradiction on a fact Worker 1 will read from both.

**Fix:** in both sites, name the constants `_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE` and say
that `_PATCH_OWNER` is the owner value they are matched against — or state the attributes by their string
values as 1b does. No spec context is needed, which is why this returns rather than escalates.

### Low:

#### L1 — "Neither touches a decision" is false of the line, true of its content

Item 23 and 1b's mirror of it describe the two-line `PLAN-024.md` delta as "mechanical reference rewrites
carrying no contract", then add "**Neither touches a decision, a DoD item, or a test name.**" Re-derived:

```shell
git show 7014125a:docs/PLAN-trac-37064-database-teardown.md > <scratch>/plan-7014125a.md
diff <scratch>/plan-7014125a.md docs/builder/temp-tests/PLAN-024.md
#   92c92  -> the AGENTS.md citation, inside decision D-4's own bullet
#   115c115 -> `spec-019-…` -> `SPECS/spec-019-…`, inside DoD item 9c
```

Line 92 **is** inside a decision bullet and line 115 **is** inside a DoD item; what neither changes is the
decision's or the item's *content*. The load-bearing clause ("carrying no contract") is exactly right and
reproduces; the reassurance sentence beside it overstates in the direction that makes it easy to accept.

**Disposition: recorded, not held.** The fix is one word ("neither changes a decision's content") and the
claim Worker 1 acts on is unaffected. Flagged here so the wording is not inherited verbatim into the
rationale, where a reader who re-derives the diff will see a decision bullet in it.

#### L2 — The build plan's "1,536-byte stub" no longer measures the file

Both artifacts head themselves with "1,618-byte stub" and `wc -c` agrees (**1618**). The build plan's
`## The input contract` says **1,536**. The build plan is not writable by this pass and is not under
review, but Slice 2 rewrites this file and may inherit the number from either place.

**Disposition: recorded for Worker 1, not held** — the artifacts are right and the discrepancy is in a
document neither this pass nor Worker 2 may edit.

### Adjudication of the recorded disagreement (1a note 24)

**The builder is upheld; the prior review's L1 progression is overruled.** Both halves, on the evidence:

- L1's **finding** — `e82df83d` adds the 12th test, not the 11th — is **correct** and is correctly applied.
  Measured: 11 at `744fd28d`, 12 at `e82df83d`.
- L1's **stated progression** — "6 -> 10 -> 11 -> 12 -> 13 -> 17 -> 17 -> 20 -> 21 across `300e2811`,
  `7014125a`, `744fd28d`, `e82df83d`, `48f9f65d`, `0d655bde`, `136c5476`, `eb2a1764`, `18550f5d`" — is
  **not wrong pair-by-pair**: every one of those nine `(commit, count)` pairs reproduces, `48f9f65d`
  included. It is wrong **as a progression**, because it omits `c7cb5f5c` and so silently attributes the
  12 -> 13 step to `48f9f65d`. Measured: `c7cb5f5c` takes 12 -> 13 by adding
  `test_apply_no_ops_when_toggle_disabled`, and `48f9f65d` is 13 -> 13, deleting two rows and adding two.

That distinction matters for what the next reader trusts, so it is stated plainly rather than as "the
review was wrong": **a per-commit count list is not a progression unless it enumerates every commit that
moved the number.** The corrected body line in both artifacts now enumerates `c7cb5f5c`, and it is the one
to trust. The builder was also right to log the disagreement instead of editing the review section
(`BUILD.md` `### The review document is evidence, not contract`); note 24's own evidence block is
reproducible as written.

### The cross-cohort conflict's deciding fact — verified

This is the fact Worker 1's change-record start point rests on, so it was re-derived from the blobs rather
than read. Read-only, outside the repo:

```shell
git show 7014125a:docs/PLAN-trac-37064-database-teardown.md > <scratch>/plan-7014125a.md
git show 7014125a:docs/TEMP-trac-37064-test-plan.md         > <scratch>/temp-7014125a.md
git show d1d19ca2^:docs/PLAN-trac-37064-database-teardown.md > <scratch>/plan-final.md
git show d1d19ca2^:docs/TEMP-trac-37064-test-plan.md         > <scratch>/temp-final.md
diff <scratch>/temp-7014125a.md docs/builder/temp-tests/TEMP-024.md   # rc=0, identical
diff <scratch>/plan-7014125a.md docs/builder/temp-tests/PLAN-024.md   # rc=1, exactly 2 changed lines
diff <scratch>/plan-final.md    docs/builder/temp-tests/PLAN-024.md   # rc=0
diff <scratch>/temp-final.md    docs/builder/temp-tests/TEMP-024.md   # rc=0
```

- The recovered `TEMP-024.md` **is byte-identical** to its `7014125a` blob. Confirmed.
- The recovered `PLAN-024.md` differs from its `7014125a` blob by **exactly two lines**, and both are the
  mechanical rewrites named (`df547235`'s line-NN sweep at line 92; `974189ad`'s `SPECS/` prefix at line
  115). Confirmed, with the one wording caveat in L1.
- Both recovered files are byte-identical to their `d1d19ca2^` blobs, so the recovery itself is faithful
  and the "as recovered" in the claim is not doing hidden work.
- The follow histories reproduce: `PLAN` has 6 revisions (`300e2811`, `61973f8d`, `7014125a`, `974189ad`,
  `df547235`, `d1d19ca2`), `TEMP` has 2 (`7014125a`, `d1d19ca2`).

**Verdict: the measurement stands, and the window does collapse to the point `7014125a`.** The derived
consequence also holds independently: `744fd28d` (2026-05-26T15:09) and `e82df83d` (15:27) both post-date
the plan's last content-bearing write at 10:21, and the `7014125a` blob of `_django_patches.py` carries
the docstring promise "logs a single ``INFO``-level notice" over an `apply()` that calls `logger.info`
unconditionally — so the **claim** was in the planned contract and the **sentinel** that made it true was
not. Worker 1 can rely on this.

**The conflict is still Worker 1's, and is not silently resolved.** 1a item 23 is headed
`[DECISION — Worker 1's, as spec custodian]`, 1b's escalation block repeats it verbatim-in-substance, both
state the two readings and what each costs, and neither picks one. Confirmed by reading both sections end
to end.

### Regression check on the repair

- **Cross-references between the artifacts agree**, on every shared fact I checked: the 21/6/15 surface
  split, the test-count progression including `c7cb5f5c`, the wrap decomposition 4 + 2 + 1, the
  `48f9f65d` / `0d655bde` split, the plan's upper bound, the catalog-is-a-union statement (present in
  both), and the escalation's framing. **One exception, M1** — `_PATCH_ORIGINAL`, where 1b is right and
  1a is wrong.
- **No row contradicts another within 1a.** The rebuilt table, the progression line beneath it, rows T-9 /
  T-10, section 7, `### Gaps found`, and notes 9 / 11 / 12 / 19 / 23 / 24 are mutually consistent, and the
  three statements of the deferred items no longer disagree with each other (the prior review's DRY
  finding about triple-statement is now a duplication without a contradiction in it).
- **`### Notes for Worker 1` is usable as the sole input to the spec rewrite.** Walked all 24 items:
  every one names a decision, a symbol, a settings key, a commit, or a file, and every conclusion carries
  re-derivable evidence beside it. The two weakest were repaired in this round — item 9 now states the
  `__all__` claim **without** the rotting count, and item 19 carries the concurrent-edit caveat and is
  still exactly true (`git show HEAD:…/_strawberry_patches.py | grep -c` -> **1**; working tree -> **0**).
  M1 is the single item that is not re-derivable as written.
- **Nothing was introduced.** No `.py`, spec, build-plan, or baseline-dirty file was modified by the
  apply-changes pass: `git status --short | grep '\.py$'` returns the one `M
  django_strawberry_framework/_strawberry_patches.py` the concurrent Slice 3 cohort owns, and
  `git diff HEAD -- django_strawberry_framework/__init__.py` is empty.

### DRY findings

The prior review's documentation-level duplication finding stands and is not aggravated: the deferred
items are still stated in three places (row 9b, `### Gaps found`, items 19-21), now consistently. Worth
one line for Worker 1 rather than a hold — the fix is Slice 2's single-sourcing of the catalog, not
another edit to this artifact. No code, no abstraction, no existence challenge.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged. An `ast` walk confirms no name containing `wrap`, `patch`, or `testing` is in the root
`__all__` at HEAD, so the claim item 9 asks the spec to carry is true as re-derived.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Its only write is this artifact.

### Failability proofs

None owed and none recorded: the pass introduces no boundary, guard, gate, or rejection path and edits
Markdown only. My independent re-run set is therefore **empty**, which `worker-3.md` makes legal in
exactly this case. No source file was mutated; the transient-mutation carve-out was not exercised.

### Hot-path budget

Not applicable; the build plan declares no hot path and this pass changes no code.

### Floor verification

**Out of scope for this pass by dispatch, and correctly not re-run by the builder.** The plan assigns the
run to Slice 1b, the prior review re-executed it in full and accepted it, and this pass's scope declares
floor verification **none**. I did not touch `/tmp/dsf-floor-024` and issued no `uv pip install`, into it
or into the shared `.venv`.

### Static helper

`scripts/review_inspect.py` **not run** — recorded skip. The pass re-derives git history and Markdown
claims rather than reviewing new logic; pre-flight already ran it on `_django_patches.py`; no
repeated-literal or import-boundary evidence was needed for any finding.

### Temp test verification

- `docs/builder/temp-tests/024-rereview/` — no temp test was needed. Every claim in scope was settled by
  read-only git and `grep`/`ast` measurement; the one instrument written (the backticked-symbol resolver
  used in the sample declaration's last row) ran as a throwaway script over the two artifacts and produced
  M1.
- Disposition: **nothing to promote.** The resolver is a weaker duplicate of the one Slice 3's reviewer
  already wrote and escalated to the maintainer as `scripts/check_citations.py`; M1 is direct evidence for
  that escalation and is noted as such below rather than as a second proposal.

### What looks solid

- **The sweep was widened past the finding.** The review named two hashes; the builder resolved all 34
  tokens and established that no third orphan hides behind them. I reproduced the sweep independently and
  got the identical 34 / 32 / 30 / 2 partition, including the two traps it names: a patch-id and a tag id
  both look like a hash, and only `cat-file -t` plus the `^{commit}` peel tell them apart.
- **The M2 fix is a split, not a translation, and the split is right in all six places.** Translating the
  two rows together — the cheap fix — would have left T-10 wrong under a *reachable* hash, which no longer
  announces itself. The `48f9f65d` blob still carrying `"""Verbatim copy of Django 5.2.13's …"""` is the
  clean proof that the two commits are different changes, and it reproduces.
- **The pass found a defect the review did not.** Entry 13's 12 -> 13 is really 13 -> 13, and the builder
  found it by re-measuring numbers it had no finding against. A `-2/+2` commit is exactly what a
  count-only record cannot see, and it is the commit where graceful degradation was retired.
- **The disagreement was logged rather than applied or dropped.** Note 24 leaves the review section intact
  and hands the adjudication to this pass with its evidence attached, which is the shape that lets a third
  party settle it in one command.
- **The plan's upper bound is now a measurement, not a guess**, and the derived "the sentinel was never
  planned" consequence survives independent derivation from the `7014125a` blob's own docstring.

### Notes for Worker 1 (spec reconciliation)

- **M1 must be closed before item 7 is written into the spec.** The reload-safety contract is real and
  correctly described; only the two symbol names are wrong. Correct form:
  `_PATCH_OWNER_ATTRIBUTE` (`"_django_strawberry_framework_patch_owner"`) and `_PATCH_ORIGINAL_ATTRIBUTE`
  (`"_django_strawberry_framework_original"`), stamped onto `_patched_remove_databases_failures` and read
  back by `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor`, with
  `_PATCH_OWNER` as the owner value they are matched against. 1b's `**Facts for the spec**` item 6 already
  states it correctly — prefer that wording.
- **The change-record starting point remains yours and is now decidable.** Both artifacts present it as
  your call with the two readings and their costs, and the deciding measurement (both planning documents
  describe the tree at exactly `7014125a`) is verified above. Nothing in this re-review narrows the choice
  further; what it does establish is that the log-once **sentinel** must not be described as a planned
  deliverable under either option.
- **Escalated (evidence for the Slice 3 maintainer decision, not a new proposal).** M1 is a second live
  instance of the ungated defect Slice 3 escalated: a symbol citation that resolves to nothing, produced
  *inside this cycle* by a pass whose whole subject was citation correctness, and caught only by a
  throwaway resolver. Two instances in one cycle is the measured cost of option 3 (status quo) in that
  escalation's own framing. Recorded here so the maintainer's choice has both data points.
- **Do not inherit L1's "neither touches a decision" wording** into the rationale; say "neither changes a
  decision's content". Do not inherit the build plan's "1,536-byte stub" (L2) — the file is **1,618**
  bytes.
- **The deferred-work catalog is the union of both cohorts' lists**, and item 19 must be re-measured
  before homing: at this pass the repair is present and uncommitted (HEAD blob 1 occurrence, working tree
  0), owned by the concurrent Slice 3 cohort.
- **HEAD has moved to `f466863a`** since both artifacts were written. No surface file changed; no number
  needs re-deriving. Do not read it as drift.

### Review outcome

`revision-needed`.

Everything the apply-changes pass was sent back for landed, and landed measured: the orphan sweep
reproduces at 34 / 32 / 30 / 2 with zero body occurrences of either dead hash, the M2 attribution is split
correctly across all six sites, every new number I re-derived is true, the disagreement it logged is
upheld, and the deciding fact for the cross-cohort conflict verifies from the blobs. The load-bearing
verdict — no code gap — is untouched and remains correct.

What holds it is one Medium: `_PATCH_ORIGINAL` names a symbol that has never existed at any revision, and
it sits in the **[SPEC]**-marked note that becomes a sentence in a permanent archived spec. The fix is two
words and needs no spec context, so the `review-accepted`-with-escalation route does not apply — the same
standard that sent 1b back for a single wrong clause. The re-pass is scoped to that citation and to L1's
one-word wording; nothing else in this artifact needs redoing, and the walk, the table, the sweep, and the
notes should be left exactly as they are.

---

## Build report (Worker 2, pass 3)

Scope: the M1 citation repair, L1's wording, L2's stale byte count, and an independent re-run of the
backticked-symbol sweep over the whole of this artifact's body. No `.py` file, no spec, no build plan,
no baseline-dirty file was touched. The two review sections and the two earlier build reports are
unedited.

### Files touched

- `docs/builder/bld-slice-1a-024-planned_vs_head.md` — three body edits (lines 173, 402-411, 503-505 as
  they stood before this pass), this report, and `Status:`.
- `docs/builder/worker-memory/worker-2-024.md` — one appended memory entry.
- `docs/builder/temp-tests/024-fix2/` — scratch: the citation resolver and one recovered `PLAN-024.md`
  blob. Not promoted (see `### Notes for Worker 3`).

### Tests added or updated

None (read-only on all source and tests).

### Findings addressed

**M1 — `_PATCH_ORIGINAL` (both sites, fixed).** The finding reproduces exactly. Measured at this pass,
whole-token, occurrences not matching lines (`grep -rno '\b<t>\b' --include='*.py' . | wc -l`):

| Token | `_django_patches.py` | tree-wide |
|---|---|---|
| `_PATCH_OWNER_ATTRIBUTE` | 3 | 9 |
| `_PATCH_ORIGINAL_ATTRIBUTE` | 3 | 9 |
| `_PATCH_OWNER` | 3 | 9 |
| `_PATCH_ORIGINAL` | **0** | **0** |

`\b` matters here and nowhere else in the sweep: without it `_PATCH_OWNER` and `_PATCH_ORIGINAL` both
"resolve" inside `_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE`, which is exactly how an invented
name reads as live. With `\b`, `_PATCH_OWNER` still returns 9 — the boundary holds because `_` is a word
character, so `_PATCH_OWNER_ATTRIBUTE` is not a match.

The mechanism the replacement text now states was re-derived from the module rather than from the
finding: `django_strawberry_framework/_django_patches.py #"_PATCH_OWNER_ATTRIBUTE = "`
and the two constants beneath it define the names; two module-scope `setattr` calls stamp them onto
`_patched_remove_databases_failures`; `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor #"if getattr(function, _PATCH_OWNER_ATTRIBUTE, None) == _PATCH_OWNER:"`
reads them back and compares the owner attribute against the `_PATCH_OWNER` **value**. Both sites now
name only existing constants and mark `_PATCH_OWNER` as a value, not an attribute — which is what
`bld-slice-1b-024-divergence_and_floor.md` entry 18 already says. The cross-cohort contradiction is
closed; 1b was not edited.

**L1 — "Neither touches a decision" (fixed).** Re-derived rather than accepted:
`diff <7014125a blob> docs/builder/temp-tests/PLAN-024.md` is exactly two hunks, `92c92` and `115c115`.
Line 92 is the body of the decision bullet "**Whether to ship a `DJANGO_STRAWBERRY_FRAMEWORK` settings
escape hatch.**" and line 115 is the "**Version target**" sub-bullet of DoD item 9. The finding is
right: the lines are inside a decision and a DoD item. Reworded to claim what is true — neither
*changes* a decision's content, a DoD item's content, or a test name. The load-bearing clause
("carrying no contract") is unchanged because it reproduces.

**L2 — the "1,536-byte stub" figure: already corrected at source, and this is a partial disagreement
with the finding.** The finding states the build plan's `## The input contract` says 1,536. It does not,
at this pass: `docs/builder/build-024-django_trac_37064_hardening-0_0_7.md` line 34 reads
"a 1,618-byte card-snapshot **stub**", and `grep -rn '1,536\|1536' docs/builder/ docs/SPECS/spec-024*`
returns three hits, **all three inside this artifact's own Worker 3 review section** (the finding text
itself) and none in the build plan. `wc -c` on the stub is **1618**, so the artifacts' figure is the
correct one. The build plan is untracked, so a concurrent pass corrected it after the review was
written. Recorded here and in `### Notes for Worker 1` as instructed; nothing to fix.

### The citation sweep, re-run over the whole body

The finding's two sites are a sample, so the class was re-measured rather than spot-fixed. Instrument
(`docs/builder/temp-tests/024-fix2/resolve_citations3.py`, written fresh for this pass): AST-walk every
non-`docs` `.py` in the tree collecting every defined name, bound name, attribute, argument, alias and
string constant plus every module stem; then take every backticked span in the artifact body, keep only
the spans that *claim to be a Python symbol* (a bare identifier, a dotted path's tail, or the
`path::Qualified` tail, with any `#"..."` anchor and `()` suffix stripped), drop keywords and hex-looking
tokens, and report whatever does not resolve. Body = the Plan section and both build reports; the two
review sections are excluded because they are not mine to edit.

**Before the fix: 12 non-resolving spans. After: 11, and the one that went is `_PATCH_ORIGINAL`.**
Adjudicated one by one:

| Span | Verdict |
|---|---|
| `_PATCH_ORIGINAL` | **invented — the defect. Fixed at both sites.** |
| `_PATCH_APPLIED` | deliberate: retired symbol, `git log --all -S` -> `300e2811`, `7014125a`. Every citation describes it as gone. **Leave.** |
| `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` | deliberate: retired at `eb2a1764`, 7 historical commits; cited as the pre-widening single pin. **Leave.** |
| `_missing_symbol_logged` | deliberate: deleted at `48f9f65d`, 9 historical commits; cited in `[RATIONALE]` item 11 as retired. **Leave.** |
| `test_apply_logs_missing_symbol_notice_only_once` | deliberate: deleted test, 9 historical commits. **Leave.** |
| `test_apply_no_ops_when_database_failure_symbol_missing` | deliberate: deleted test, 6 historical commits. **Leave.** |
| `MultiDBTestCase` | not a symbol claim — row S-1 cites it explicitly as *not existing*. **Leave.** |
| `django_trac_37064_hardening_safe_wrap_connection_method` | a `docs/GLOSSARY.md` anchor, not a Python name. Instrument false positive. |
| `tearDown` | resolves: 4 occurrences in `django_strawberry_framework/testing/_wrap.py`, all inside the docstring example. The instrument misses docstring-embedded names. False positive. |
| `wontfix` | a Django ticket status quoted from the plan. False positive. |
| `grep`, `.venv` | a shell command and a directory. False positives. |

So the population is **1 invented name, 5 deliberate retired-symbol citations, 6 non-symbols**. The
retired-symbol five are all in retirement-describing prose, which is the only place they may appear.

My count differs from the review's ("9 non-resolvers in 1a") because the instruments differ — mine
resolves against string constants and module stems too, and it sweeps only the body. The two agree on
the thing that matters: **one** span in this artifact is an invented name, and it is `_PATCH_ORIGINAL`.

### [SPEC] / [RATIONALE] internal consistency after the fix

Re-ran the resolver over `### Notes for Worker 1` alone (the section Worker 1 copies verbatim). Before
the fix: 4 non-resolvers — `_PATCH_ORIGINAL` (item 7, **[SPEC]**), `_PATCH_APPLIED` (item 17 and note
19, both **[RATIONALE]**), `_missing_symbol_logged` (item 11, **[RATIONALE]**), `tearDown` (item 1, a
false positive that resolves in `_wrap.py`). After the fix: 3, **and every remaining one sits in a
[RATIONALE] item that exists to record the symbol as retired.** No **[SPEC]** item now names a symbol
absent from HEAD. That is the invariant the finding actually protects, and it now holds.

### Failability proofs

None; this pass introduced no boundary, guard, gate, or rejection path, and edits Markdown only.

### Hot-path budget

Not applicable; the plan declares no hot path and this pass changes no code.

### Floor verification

Not applicable; dispatch declares floor scope **none**. `/tmp/dsf-floor-024` was not touched, no
`uv pip install` was issued, and the shared `.venv` was not mutated.

### Validation run

- No ruff run: this pass touched no `.py` file. The scratch resolver under
  `docs/builder/temp-tests/024-fix2/` is a throwaway instrument outside the package and test trees.
- No `pytest`: no source or test changed, so there is nothing to re-run and no test-staleness surface.
  No `--cov*` flag was used anywhere in this pass.
- `git status --short` after the pass: the one artifact modified here, the scratch directory, and the
  baseline-dirty set the build plan lists. Nothing else. `git status --short | grep '\.py$'` shows only
  the `_strawberry_patches.py` and `optimizer/hints.py` entries owned by concurrent cohorts — not
  touched here, not reverted.
- HEAD is `f466863a`. It touches none of card 024's six surface files, so every count already in this
  artifact still stands and was not re-derived.

### Implementation notes

- **Both sites were rewritten, not minimally patched.** The finding calls the fix "two words". It is
  not: the sentence is wrong in two independent ways — one name never existed, and the other is a value
  cited as an attribute — so a straight substitution to `_PATCH_ORIGINAL_ATTRIBUTE` would have left
  `_PATCH_OWNER` still described as an attribute, and the corrected half would then be the harder error
  to see because every token would resolve. Both sites now distinguish attribute-name constant from
  owner value explicitly.
- **The `[SPEC]` site carries the string values, the table row does not.** Item 7 becomes spec prose, so
  it states `"_django_strawberry_framework_patch_owner"` / `"_django_strawberry_framework_original"`
  inline, matching 1b's wording. The `18550f5d` table row is a one-line change summary; adding the
  string values there would restate 1b's entry 18 in a cell.
- **L1's reword names the two sites rather than softening the claim.** "Neither changes a decision's
  content" would be true but would hide that a reader re-deriving the diff *will* see a decision bullet
  in it. The wording now says where the lines live and what they leave unchanged.

### Notes for Worker 3

- The resolver in `docs/builder/temp-tests/024-fix2/` is **not for promotion**: it is a weaker duplicate
  of the instrument the prior reviewer already escalated to the maintainer as a possible
  `scripts/check_citations.py`. It is left in scratch so the sweep is reproducible against this exact
  artifact, and it dies with the cycle.
- To reproduce the sweep after any further edit, re-derive the section boundaries first — my line ranges
  (`1:557`, `864:1067`) shifted when this report was appended, and a stale range silently sweeps a review
  section or misses part of the body.
- The three body edits are the whole diff of this pass. Nothing in the walk, the rebuilt commit table,
  the hash sweep, the progression line, or the 24 notes was otherwise altered.

### Notes for Worker 1 (spec reconciliation)

- **Item 7 is now safe to copy verbatim.** All three constants exist at HEAD (`_PATCH_OWNER_ATTRIBUTE`,
  `_PATCH_ORIGINAL_ATTRIBUTE`, `_PATCH_OWNER`, 3 occurrences each in
  `django_strawberry_framework/_django_patches.py`, 9 tree-wide), and the item now states which two are
  attribute names and which one is the owner value. It agrees with
  `bld-slice-1b-024-divergence_and_floor.md` entry 18 word for word in substance.
- **No `[SPEC]` item names a symbol absent from HEAD.** Re-measured after the fix; the three remaining
  non-resolving names in the notes section are all inside `[RATIONALE]` items whose whole purpose is to
  record them as retired (`_PATCH_APPLIED`, `_missing_symbol_logged`, and `tearDown`, which is a
  false positive and does resolve).
- **L2 is already closed at source, contrary to the finding as written.** The build plan's
  `## The input contract` reads **1,618** at line 34, not 1,536; the only three occurrences of "1,536"
  anywhere under `docs/builder/` are inside this artifact's own Worker 3 review section. `wc -c` on
  `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` is **1618**. Nothing needs correcting in
  the build plan; do not re-issue the correction against it.
- **L1's wording must not be inherited as originally written.** The replacement is on disk in this
  artifact. Recommended spec/rationale wording, should the point be restated there:
  - where it lives: the rationale's account of the recovered planning documents, under whatever heading
    carries the two-line `PLAN-024.md` delta.
  - current wording: "Neither touches a decision, a DoD item, or a test name."
  - recommended replacement: "Line 92 sits inside decision D-4's own bullet and line 115 inside DoD item
    9's version-target sub-bullet; what neither changes is a decision's content, a DoD item's content,
    or a test name."
- Everything else in this artifact is unchanged from the state the pass-2 review accepted on the merits.


---

## Review (Worker 3, pass 3)

Third-pass review, deliberately narrow. Everything the pass-2 review accepted on the merits — the hash
sweep, the M2 attribution split, the corrected progression, the counts, the cross-cohort deciding fact,
the two load-bearing verdicts (**no code gap**, **floor pass**) — is not re-opened and was not re-run.
The subject is the one Medium that held the artifact (M1), the two Lows beside it, and whether closing
them broke anything.

Tree state: `HEAD` is still **`f466863a`**, unmoved since the pass-2 review, so every count already in
this artifact stands unre-derived. `git status --short` shows no `.py` file touched by this pass; the
`_strawberry_patches.py` / `optimizer/hints.py` entries belong to concurrent cohorts and were neither
touched nor reverted.

### Sample declaration: what I re-derived, and what I accepted unchecked

| Claim | Command | Result |
|---|---|---|
| the four constants, whole-token, occurrences not lines | `grep -rno '\b<t>\b' --include='*.py' . \| wc -l` and the same over `_django_patches.py` | `_PATCH_OWNER_ATTRIBUTE` **3 / 9**, `_PATCH_ORIGINAL_ATTRIBUTE` **3 / 9**, `_PATCH_OWNER` **3 / 9**, `_PATCH_ORIGINAL` **0 / 0**. Reproduces cell for cell. `_` is a word character, so `\b_PATCH_OWNER\b` genuinely excludes `_PATCH_OWNER_ATTRIBUTE` — the 9 is standalone occurrences, not the substring trap |
| the mechanism, read from the module not the report | `grep -n '_PATCH_OWNER\|_PATCH_ORIGINAL' django_strawberry_framework/_django_patches.py` | **132-134** define the three constants; **345** and **346-350** are the two module-scope `setattr` calls onto `_patched_remove_databases_failures`; **149-150** read them back inside `_captured_upstream_descriptor`. The builder's line citations are right and the code does what the replacement text says |
| `_PATCH_ORIGINAL` is gone from the body | AST-backed resolver over `1:557`, `864:1067`, `1397:end` | occurrences at **1418, 1426, 1428, 1470, 1475, 1492, 1497 only** — every one inside the pass-3 build report describing the fix. **0 in the pre-existing body**; the pass-2 review section's occurrences are the record and stayed untouched |
| both fixed sites name only live symbols | read lines 173 and 402-411 against the module | line 173 names `_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE` and marks `_PATCH_OWNER` the owner *value*; item 7 states both string values verbatim — `"_django_strawberry_framework_patch_owner"` and `"_django_strawberry_framework_original"` — and both match the module byte for byte |
| cross-cohort agreement | read `bld-slice-1b-024-divergence_and_floor.md` lines 397-403 (read-only) | 1b names the same four symbols with the same two string values and the same "two `setattr` calls after the function definition" mechanism. **The contradiction is closed**; 1b was not written to |
| the 5 "deliberate retired-symbol" citations really are retired | `grep -rno '\b<t>\b' --include='*.py' .` and `git log --all --oneline -S'<t>' -- <pkg> <tests>` | live occurrences **0 for all five**; history **7 / 9 / 9 / 6 / 2** for `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`, `_missing_symbol_logged`, `test_apply_logs_missing_symbol_notice_only_once`, `test_apply_no_ops_when_database_failure_symbol_missing`, `_PATCH_APPLIED` — the builder's per-token numbers reproduce, and `_PATCH_APPLIED`'s two commits are exactly `300e2811`, `7014125a` as claimed |
| each of the five is cited *as gone*, never as live | read every body occurrence (lines 155, 158, 159, 168, 169, 215, 273, 316, 434, 467, 485) | every one sits in retirement-describing prose ("deleted", "retired", "-> `_patch_is_installed()`", "renamed away at `eb2a1764`"). No citation asserts a live symbol |
| **no `[SPEC]` item names a symbol absent from HEAD** | enumerate all `[SPEC]`-marked items (**exactly 9**, lines 374-421), then whole-token `grep -rno` per symbol | all resolve: `safe_wrap_connection_method` 22, `_DatabaseFailure` 44, `APPLY_UPSTREAM_PATCHES` 80, `UPSTREAM_PATCH_DEPENDENCIES` 14, `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` 8, `_disallowed_connection_methods` 18, `disallowed_simple_test_case_connection_methods` 11, `_patch_is_installed` 73, `_patched_remove_databases_failures` 14, `_captured_upstream_descriptor` 2, `DjangoStrawberryFrameworkConfig` 19, `_django_patches` 84, `_strawberry_patches` 25, `_cross_web_patches` 20, `upstream_patches_enabled` 30, plus the three `_PATCH_*` constants. `tests/testing/test_wrap.py` and `django_strawberry_framework/testing/__init__.py` exist; `django_strawberry_framework/test` does **not**, which item 2 asserts; `e145ba36` is a HEAD ancestor. **The invariant holds** |
| the builder's self-reported blind spot | my resolver indexes docstring string constants too | `tearDown` resolves — **4 whole-token occurrences** in `django_strawberry_framework/testing/_wrap.py` (82, 105, 108, 111), all inside docstrings; `tearDownClass` correctly excluded by `\b`. Confirms it is a false positive, not a citation defect |
| the population, on an independent instrument | AST walk of every non-`docs` `.py` (defs, names, attributes, args, aliases, module stems, docstring words) vs every backticked span in the body | **9 distinct non-resolving spans**: the 5 retired symbols, `MultiDBTestCase` (cited as absent), the `docs/GLOSSARY.md` anchor, `Qualified` (from the instrument-description prose `path::Qualified`), and `_PATCH_ORIGINAL` **in the fix-describing report only**. No invented name survives anywhere in the body |
| L1's reword | `git show 7014125a:docs/PLAN-trac-37064-database-teardown.md` into `/tmp`, `diff` against `docs/builder/temp-tests/PLAN-024.md` | exactly **two hunks**, `92c92` and `115c115`. Line 92 is the body of the escape-hatch decision (the artifact's D-4) and line 115 the "**Version target**" sub-bullet of DoD item 9. The reword on disk says exactly that |
| L2, both halves | `sed -n '34p'` on the build plan; `wc -c` on the spec; `grep -rno '1,536\|1536' docs/builder/ docs/SPECS/` | plan line 34 reads **"a 1,618-byte card-snapshot stub"**; `wc -c` = **1618**; "1,536" occurs **only** in this artifact (pass-2 review section 1189/1192/1370, then the pass-3 report's own quotation of the finding) and in `worker-memory/worker-2-024.md`. **Zero occurrences in the build plan** |
| public surface | `git diff HEAD -- django_strawberry_framework/__init__.py` | **empty** |

**Accepted unchecked (named, so the sample is honest):** the pass-3 report's own "12 before / 11 after"
intermediate — instrument-dependent by construction, and the load-bearing subset (which spans are
invented) re-derived exactly on my instrument; everything the pass-2 review accepted on the merits; the
floor venv; the planned-contract walk; the classification prose of the 24 notes.

### High:

None.

### Medium:

None. M1 is closed at both sites, verified against the module rather than against the finding.

### Low:

#### L1 (pass 3) — item 7's plural says both attributes are "matched against" the owner value; only one is

Line 408-410, inside a **[SPEC]** item Worker 1 copies verbatim:

```docs/builder/bld-slice-1a-024-planned_vs_head.md:408
`_PATCH_OWNER` (`"django_strawberry_framework._django_patches"`), is the owner **value** those
attributes are matched against — not an attribute name — and …
```

The module compares exactly one of them:

```django_strawberry_framework/_django_patches.py:149:150
    if getattr(function, _PATCH_OWNER_ATTRIBUTE, None) == _PATCH_OWNER:
        return getattr(function, _PATCH_ORIGINAL_ATTRIBUTE, None)
```

`_PATCH_ORIGINAL_ATTRIBUTE`'s value is the captured descriptor, **returned**, never compared with
anything. The load-bearing half of the repair is right — the two attribute-name constants are named
correctly and `_PATCH_OWNER` is correctly marked a value rather than an attribute — so this is the
plural over-reaching by one, in the same direction as the pass-2 L1 it sits next to.

**Recommended wording:** "… is the owner **value** that the *first* of those attributes is matched
against — not an attribute name — and `_captured_upstream_descriptor` returns the second when the match
holds."

**Disposition: recorded, not held.** Every symbol resolves, the value-vs-attribute distinction the
finding existed to fix is correct, and 1b's mirror ("the two owner attributes are stamped onto …") is
loose in the same direction, so this is not a cross-cohort conflict. Flagged only because it lands in a
permanent spec.

### Adjudication of the recorded disagreement (pass-2 L2, the "1,536-byte stub")

**The builder is upheld. The number to trust is 1,618.** Measured at this pass:

```shell
sed -n '34p' docs/builder/build-024-django_trac_37064_hardening-0_0_7.md
#   The archived spec is a 1,618-byte card-snapshot **stub** — …
wc -c docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md      # 1618
grep -rno '1,536\|1536' docs/builder/ docs/SPECS/
#   bld-slice-1a-…:1189, 1192, 1370   <- the pass-2 review section, i.e. the finding's own text
#   bld-slice-1a-…:1450, 1451, 1453   <- the pass-3 report quoting the finding
#   worker-memory/worker-2-024.md:76, 77
#   (nothing in build-024-…, nothing in docs/SPECS/)
```

Both halves of the builder's account reproduce: the plan reads 1,618, and every "1,536" under
`docs/builder/` is this artifact quoting the finding. The three pre-pass-3 occurrences the builder
counted are lines 1189, 1192 and 1370 — one occurrence each, so its `grep -rn` line count and the
occurrence count coincide here and the number is sound either way.

What cannot be settled: the build plan is **untracked**, so it has no history and there is no read-only
way to establish what line 34 said when the pass-2 review measured it. The two accounts are therefore
compatible — a concurrent pass correcting the plan between the two passes explains both — and neither
worker is convicted of a bad measurement. For the next reader: **1,618 is the file, everywhere; 1,536 is
dead and exists only as quoted finding text.** Slice 2 must not inherit it from either document.

### Regression check on the repair

The pass touched three body spans and appended a report. Checked for collateral:

- Line 173's table row still carries its other content unchanged (`hasattr(cls, …)` -> validated body
  source, "Tests 20 -> 21") — the repair replaced only the parenthetical.
- Item 7's other claims survive: `_patch_is_installed()` resolves (73 occurrences), the
  `importlib.reload()` rationale matches `_captured_upstream_descriptor`'s docstring, and
  `_patched_remove_databases_failures` is the stamped function at line 345.
- The L1 reword left the load-bearing clause ("mechanical reference rewrites carrying no contract")
  intact, which is the clause that reproduces.
- The two prior review sections and the two earlier build reports are unedited — `_PATCH_ORIGINAL` still
  reads exactly as the pass-2 finding wrote it at 1129-1164, which is what makes the record legible.
- Markdown scaffold intact: the single `<!-- LINK DEFINITIONS -->` delimiter with all ten canonical
  group headers is still the last block in the file.

### DRY findings

None new. The pass-3 resolver duplicates the pass-2 reviewer's instrument, which the builder itself
flags and declines to promote; the standing recommendation for one shared `scripts/check_citations.py`
is already escalated to the maintainer and is unchanged by this pass.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export
list are unchanged; this pass edits Markdown only.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. (`CHANGELOG.md` is dirty at baseline and belongs to
a concurrent session; it was neither read as this slice's product nor touched.)

### Documentation / release sanity

The only surface this pass touches is its own per-cycle artifact, which is exempt from the
symbol-qualified-path rule per `START.md` "Temp artifact conventions". No spec, no KANBAN, no release
metadata, no archived spec was modified. The `[SPEC]` notes destined for the permanent spec were swept
for absent symbols and are clean (see the sample table).

### Failability proofs

None owed and none run: this pass introduces no boundary, guard, gate, or rejection path, and edits
Markdown only (`BUILD.md` `### What needs a proof, and what does not`). The re-run set is therefore
legitimately **empty** — no boundary in the diff meets the mandatory floor.

### Hot-path budget

Not applicable; the plan declares no hot path and the pass changes no code.

### Floor verification

Not applicable; dispatch declares floor scope **none** and it was already verified and accepted. No
scratch venv was built, no `uv pip install` was issued, and the shared `.venv` was not mutated.

### Static helper

`scripts/review_inspect.py` not run. Skip reason: the pass's entire diff is Markdown inside one
per-cycle artifact; the helper reports on Python control flow and repeated literals and has no input
here.

### Temp test verification

- `docs/builder/temp-tests/024-review3/resolve.py` — an independent AST-backed citation resolver written
  for this pass, indexing defined names, bound names, attributes, args, aliases, module stems **and
  docstring string constants** (which is why `tearDown` resolves on it and not on the builder's).
- Disposition: **not promoted.** It is a third near-copy of the same instrument; the right home is the
  already-escalated `scripts/check_citations.py`, not another scratch file. Dies with the cycle.
- No `pytest` was run in this pass, with or without coverage flags.

### What looks solid

- The repair was made **from the module**, not from the finding. The builder re-derived lines 132-134 /
  345-348 / 149-150 itself, which is why the replacement text is right about the thing the finding did
  not state — that `_captured_upstream_descriptor` reads the attributes back off the function object.
- Refusing the minimal substitution was the right call and the report says why: swapping in
  `_PATCH_ORIGINAL_ATTRIBUTE` alone would have left `_PATCH_OWNER` described as an attribute, and every
  token would then resolve, making the surviving error strictly harder to find than the one it replaced.
- Re-measuring the **class** rather than spot-fixing two sites. The sweep is the reason I can say the
  `[SPEC]` invariant holds rather than that two lines were edited.
- The `\b` note is not padding: it names the exact instrument defect that lets an invented name read as
  live, and it is the reason my re-derivation and the builder's agree.
- Self-reporting the `tearDown` blind spot instead of recording 11 clean spans. A named blind spot is
  what let me close it in one command.
- The L2 disagreement is recorded as a disagreement, with the evidence for its own side, rather than
  either silently complied with or silently dropped.

### Notes for Worker 1 (spec reconciliation)

- **Item 7 is safe to copy verbatim, with one word to fix on the way in.** All three constants exist at
  HEAD and the string values are exact. The one imprecision is the plural in "those attributes are
  matched against" — only `_PATCH_OWNER_ATTRIBUTE` is compared with `_PATCH_OWNER`;
  `_PATCH_ORIGINAL_ATTRIBUTE` is read and returned. Recommended replacement wording is in L1 above.
- **The stub is 1,618 bytes.** Adjudicated above: the artifacts and the build plan now agree, and 1,536
  survives only as quoted finding text inside this artifact and in Worker 2's memory file. Do not
  re-issue the pass-2 correction against the build plan, and do not let 1,536 reach the rationale.
- **No `[SPEC]` item names a symbol absent from HEAD** — independently re-derived over all nine of them,
  not accepted from the build report. This is the invariant that matters for the archived spec, and it
  holds.
- The five retired-symbol citations (`_PATCH_APPLIED`, `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`,
  `_missing_symbol_logged`, and the two deleted test names) are all in `[RATIONALE]` items and all
  correctly described as gone. They must stay spelled as they are — a rationale's job is citing dead
  symbols — but they must not migrate into a `[SPEC]` item.
- Everything else in this artifact is unchanged from the state pass 2 accepted on the merits.

### Review outcome

`review-accepted`.

The Medium that held the artifact is closed and closing it broke nothing: `_PATCH_ORIGINAL` has zero
whole-token occurrences in the body, both former sites name only symbols that exist at HEAD, the
attribute-vs-value distinction is correct against the module, and 1a and 1b now say the same thing about
all four reload-safety names. The `[SPEC]` invariant the finding actually protected — no spec-bound note
citing a symbol absent from HEAD — was re-derived independently over all nine `[SPEC]` items and holds.
One Low is recorded with a disposition and a recommended wording; per `worker-3.md`'s acceptance gate a
Low with a recorded disposition does not block acceptance. On the recorded disagreement the builder is
upheld: the stub is **1,618** bytes.

---

## Final verification (Worker 1)

Slice contract, from the build plan's `## Declarations`: "did anything planned get skipped, dropped, or
silently changed?", read-only on all source, writing this artifact only. Delivered.

- **Spec slice checklist:** none exists — the archived spec was a stub with no `## Slice checklist`, and the
  artifact records that correctly rather than inventing boxes. Nothing to audit, nothing to un-tick, no
  deferral owed.
- **Scope respected:** `git diff HEAD --stat` shows one `.py` file dirty, `_strawberry_patches.py`, which is
  Slice 3's diff and not this cohort's. No spec, build-plan, or baseline-dirty file was written by it.
- **Claims re-derived by this pass rather than accepted** (`worker-1.md` `### Verifying relocation /
  promotion claims`): the `--follow` union over the six surface files is **23**, minus `b972cd84` /
  `dfa035b4` = **21 surface commits**, split **6 in-tag / 15 post-tag** by
  `git merge-base --is-ancestor <sha> 0.0.7` — reproduces cell for cell. The test-count progression
  reproduces per commit at 6, 10, 11, 12, 13, 13, 17, 17, 20, 21 across `300e2811`, `7014125a`, `744fd28d`,
  `e82df83d`, `c7cb5f5c`, `48f9f65d`, `0d655bde`, `136c5476`, `eb2a1764`, `18550f5d`, including entry 13's
  corrected net-zero step. `_django_patches.py` is 91 lines at the ship and 406 at HEAD. HEAD test counts
  are 21 / 7 / 8 = 36.
- **The citation invariant the artifact was held on holds at close.** Every backticked identifier in
  `### Notes for Worker 1` was resolved whole-token against the tree by this pass: the only non-resolving
  names are `_PATCH_APPLIED`, `_missing_symbol_logged`, and the two deleted test names, all inside
  `[RATIONALE]` items that exist to record them as retired. `_PATCH_ORIGINAL` has **0** whole-token
  occurrences outside the passages describing its own repair. No `[SPEC]` item names a symbol absent from
  HEAD.
- **Hash reachability re-checked against a moved HEAD.** HEAD is `f466863a`, not the `36cd1925` this
  artifact records. Every commit this pass carried forward into the spec and rationale was re-proved with
  `git merge-base --is-ancestor <sha> HEAD` at close — 27 distinct tokens, all reachable. Nothing from this
  artifact's body was copied on trust.
- **Escalations discharged.** The change-record starting point was decided by this pass and is recorded in
  `docs/builder/bld-slice-2-024-spec_reconciliation.md` under `### Spec changes made (Worker 1 only)`; the
  deciding measurement was re-derived from the blobs, not inherited. Item 9's no-count instruction, item 7's
  corrected reload-safety names, the L1 wording replacement, and the `1,618` figure were all honoured in the
  rewritten spec. The one Low left open at acceptance — item 7's plural over-reaching by one — was fixed on
  the way in: the spec states that `_captured_upstream_descriptor` compares the owner attribute against
  `_PATCH_OWNER` and returns the original attribute's value.
- **Deferred work:** this artifact's items 19-22 are carried into the Slice 2 artifact's deferred-work
  catalog as part of the union with 1b and 3, each re-derived rather than copied. Item 19 was re-measured at
  close: the repair is present and uncommitted (working tree 0 whole-token occurrences, HEAD blob 1).
- **Focused tests re-run:** `uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py
  tests/test_apps.py tests/test_strawberry_patches.py --no-cov -q` -> 91 passed. No `--cov*` flag.

Status: final-accepted.

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
