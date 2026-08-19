# Build: Slice 1b — Post-ship divergence catalog + floor verification

Spec reference: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` (whole file; 1,618 bytes, a card-snapshot stub with no slice checklist)
Status: final-accepted

## Plan (Worker 1)

This cohort has no separately authored Worker 1 plan section. Its contract is the build
plan `docs/builder/build-024-django_trac_37064_hardening-0_0_7.md` `## Declarations`, quoted:

> Slice 1b — writes `docs/builder/bld-slice-1b-024-divergence_and_floor.md` only. Read-only on all
> source. Question: what changed after the ship, why, and which changes flipped a contract? Also
> owns the floor run.

and its `**Floor-verification scope:**` bullet, which assigns one focused floor run to this pass:
`tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py` at Django 5.2.16 /
Python 3.10 / strawberry-graphql 0.316.0.

### DRY analysis

Not applicable; this pass is read-only on all source and adds no code.

### Implementation steps

Not applicable; audit pass. See `### Post-ship divergence catalog` below for what was performed.

### Test additions / updates

None. This pass writes no test.

### Implementation discretion items

None.

### Spec slice checklist (verbatim)

Not applicable; the archived spec is a card-snapshot stub and carries no `## Slice checklist`
section to copy. The build plan records the same fact under `## The input contract (recovered, not
invented)`.

---

## Build report (Worker 2)

### Files touched

- `docs/builder/bld-slice-1b-024-divergence_and_floor.md` — this artifact (created).
- `docs/builder/worker-memory/worker-2-024.md` — one appended entry (gitignored, append-only,
  shared with the concurrent Slice 1a cohort).

No `.py` source or test file was modified. This pass is read-only on all source, as the ownership
partition requires.

### Tests added or updated

None.

---

### Correction to the dispatch's own framing (measured, not inherited)

Two claims arrived with the dispatch and are wrong as stated. Both are recorded here because the
rewritten spec and the rationale companion inherit them if nobody re-derives them.

**1. Five of the dispatch's thirteen listed commits — equivalently, six of the twenty-one surface commits
— are INSIDE the 0.0.7 release, not post-ship.** Two populations, two correct numbers, and pass 1 stated
the headline against one and the table below against the other, which reads as a contradiction to anyone
who checks either against the other. The dispatch's 13 is the `_django_patches.py` file history and holds
5 in-tag; the surface is 21 commits across the six files and holds 6 in-tag (the extra is `e82df83d`,
which touches `tests/test_django_patches.py` only). Tag `0.0.7`
resolves to `72f6cd9b` (2026-05-27), and the `_django_patches.py` blob at that tag is
byte-identical to the blob at `744fd28d`:

```shell
git rev-parse 0.0.7                       # -> e2765ff31f63e35a3eeace026c5ab7ac70a40aae
git log -1 --format='%h %cd %s' --date=short 0.0.7
#   72f6cd9b 2026-05-27 Insert TODO-ALPHA-023-0.0.8 (DjangoType DX cleanup pass) + renumber cascade
git show 0.0.7:django_strawberry_framework/_django_patches.py > /tmp/dsf-024-scratch/patches-tag007.py
diff -q /tmp/dsf-024-scratch/patches-tag007.py /tmp/dsf-024-scratch/patches-744fd28d.py   # (no output)
```

Ancestry, measured for every commit (`git merge-base --is-ancestor <c> 0.0.7`):

| In tag `0.0.7` (6) | Post-tag (15) |
|---|---|
| `300e2811`, `893465a5`, `61973f8d`, `7014125a`, `744fd28d`, `e82df83d` | `52d97ec0`, `e145ba36`, `b8a8a6e0`, `7cc163db`, `4a25bf42`, `7c2a63ed`, `c7cb5f5c`, `48f9f65d`, `0d655bde`, `136c5476`, `5a74d803`, `eb2a1764`, `18550f5d`, `f7fbead4`, `36cd1925` |

So `7014125a` and `744fd28d` — the SimpleTestCase retarget, the guarded import, the
`_patch_is_installed` rewrite, the callable guard, the log-once sentinel — are **in-release
corrections of the same 0.0.7 ship**, not later divergence. They still rewrite the contract (see
`### Contract flips`), but the rationale companion must not describe them as post-ship changes.

**2. The dispatch's commit ordering is wrong for three commits.** It lists `7cc163db`, `4a25bf42`,
`e145ba36` in that order. The actual commit dates are `e145ba36` 2026-06-01 -> `7cc163db`
2026-06-10 -> `4a25bf42` 2026-06-12. Read in the dispatch's order, the `e145ba36` diff appears to
*reintroduce* em-dashes that `7cc163db` removed; read chronologically, `e145ba36` is a `test` ->
`testing` rename that predates the ASCII sweep. Every diff below is taken in the corrected order.

### Verified commit population

Commands (all read-only; each result is the line count of the command's output):

```shell
git log --oneline --follow -- django_strawberry_framework/_django_patches.py   # 13
git log --oneline --follow -- django_strawberry_framework/testing/_wrap.py     #  8
git log --oneline --follow -- django_strawberry_framework/apps.py              #  8
git log --oneline --follow -- tests/test_django_patches.py                     # 13
git log --oneline --follow -- tests/testing/test_wrap.py                       #  7
git log --oneline --follow -- tests/test_apps.py                               #  9
```

Union of the six, deduplicated: **23** distinct commits. Two of them (`b972cd84`, `dfa035b4`,
both 2026-05-21) touch `apps.py`/`tests/test_apps.py` only and predate the patch entirely — they
are spec-017 AppConfig work. **21 commits touch the Trac #37064 surface.** The dispatch's list of
13 is exactly the `_django_patches.py` history and is complete for that file; it misses the 8
others surfaced by following the sibling files.

Read-only blob extraction used throughout (no `stash`, no `checkout`, no `restore`, no `worktree`):

```shell
mkdir -p /tmp/dsf-024-scratch
git show <rev>:django_strawberry_framework/_django_patches.py > /tmp/dsf-024-scratch/patches-<rev>.py
diff -u /tmp/dsf-024-scratch/patches-<a>.py /tmp/dsf-024-scratch/patches-<b>.py
```

`git show 18550f5d:django_strawberry_framework/_django_patches.py` diffs clean against the working
tree file, so HEAD's blob is `18550f5d`'s and the file is not dirty in this tree.

---

### Post-ship divergence catalog

Each entry is labelled `correction` (it repairs a defect in what shipped) or `serves-later-work`
(it widens or re-shapes the surface to serve a change whose driver is elsewhere). Where the commit
message does not state the cause, the cause is marked **inference** and the diff evidence is given.

#### 0. `300e2811` — the ship (baseline, not a divergence) — IN 0.0.7

`django_strawberry_framework/_django_patches.py` created (3,855 bytes): module docstring,
unguarded `from django.test.testcases import TransactionTestCase, _DatabaseFailure`,
`_PATCH_APPLIED` bool, `_patched_remove_databases_failures`, `apply()`.
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` created, calling
`apply()`. `tests/test_django_patches.py` created with 6 tests
(`git show 300e2811:tests/test_django_patches.py | grep -c '^def test_'` -> 6).

#### 1. `893465a5` — docstring only — IN 0.0.7 — `serves-later-work`

**What:** `_django_patches.py` module docstring gains an `Ecosystem precedent` section (the
`django-debug-toolbar` `wrap_cursor` isinstance precedent, the wrap-time/unwrap-time
defense-in-depth framing) and `_patched_remove_databases_failures.__doc__` gains the mirror
paragraph. 3,855 -> 6,489 bytes.
**Why:** the commit subject states it: document the precedent and the framing. The docstring
explicitly names a *future* card that "may ship a consumer-facing helper
(`safe_wrap_connection_method`) ... that is out of scope here."
**Behavior:** none. Zero executable lines changed (`diff -u` shows docstring hunks only).
**Classification:** `serves-later-work` — it stages the vocabulary the next commit's helper needs.
Not cosmetic: the framing it introduces is load-bearing prose the spec must now carry.

#### 2. `61973f8d` — ships `safe_wrap_connection_method` — IN 0.0.7 — `serves-later-work`

**What:** new module `django_strawberry_framework/test/_wrap.py` (5,706 bytes) exporting
`safe_wrap_connection_method(connection, method_name, wrapper) -> bool`; imports
`_DatabaseFailure` directly from `django.test.testcases`; returns `False` (declines) when the
current attribute is a `_DatabaseFailure`, else `setattr`s and returns `True`. 4 tests. In
`_django_patches.py`, the "a future card may ship" paragraph is rewritten to point at the shipped
helper.
**Why:** commit subject — "wrap-time mirror of Trac #37064 patch". Completes the two-half defense
the previous commit's docstring described.
**Classification:** `serves-later-work` relative to the unwrap patch (it adds a second, cooperative
half rather than fixing the first), and it is the second of the card's two `## Other` bullets, so
it is in the card's own scope.

#### 3. `7014125a` — the four-part hardening — IN 0.0.7 — `correction` (all four)

Commit body names all four and calls them "three correctness issues in the just-shipped Trac #37064
hardening surface" (the body then lists four bullets — the message's own count is off by one).

- **Retarget `TransactionTestCase` -> `SimpleTestCase`.** `apply()` now sets
  `SimpleTestCase._remove_databases_failures`; module docstring, `apps.py::…ready` docstring, and
  `_wrap.py`'s `_add_databases_failures` reference all follow. **Why (stated):** Django defines the
  method on `SimpleTestCase`, so direct `SimpleTestCase` subclasses bypassed the net entirely.
  This is a **correctness defect in the ship**: the patch did not cover the class Django defines
  the method on.
- **Guarded import.** `from django.test.testcases import _DatabaseFailure` moves into
  `try/except ImportError: _DatabaseFailure = None`, and a new module-level predicate
  `_is_database_failure(method)` replaces the inline `isinstance`. `_wrap.py` switches from
  importing `_DatabaseFailure` to importing `_is_database_failure` from `_django_patches`.
  **Why (stated):** an unguarded private-symbol import would break package loading on a future
  Django. This creates the `testing -> _django_patches` import edge that still exists at HEAD.
- **`_PATCH_APPLIED` -> `_patch_is_installed()`.** The module-global bool is deleted; `apply()`
  now reads `SimpleTestCase.__dict__.get("_remove_databases_failures")` and compares `__func__`
  identity. **Why (stated):** the bool "did not match the docstring's 're-entrant calls are no-ops'
  promise — a third party reverting the class attribute would leave `apply()` thinking it had
  already done the work." A shipped docstring promise the shipped code did not keep.
- **`safe_wrap_connection_method` callable guard.** `raise TypeError(...)` when `wrapper` is not
  callable, ahead of the isinstance check. **Why (stated):** surface a typo at the wrap site rather
  than deep in Django's ORM stack.

Test counts, both re-measured in pass 2 with `git show "<sha>:<path>" | grep -c '^def test_'`:
`tests/test_django_patches.py` **6 -> 10**, and `tests/test/test_wrap.py` **4 -> 6** — *not* unchanged, as
pass 1 wrote. The entry's own third and fourth bullets are why: the guarded-import /
`_is_database_failure` change and the `safe_wrap_connection_method` callable guard each landed with a
test. By name, `7014125a` adds `test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`
and `test_safe_wrap_connection_method_raises_on_non_callable_wrapper`.

The correction matters past arithmetic, because it moves which commit the wrap file's coverage is
attributed to. The 7 wrap tests at HEAD decompose **4** (`61973f8d`) **+ 2** (`7014125a`) **+ 1**
(`f7fbead4`) = 7, and only the last of those three is what entry 19 records. Under the old sentence the
two `7014125a` tests appear to arrive at `f7fbead4`, which would put the `TypeError` boundary's coverage
on the commit that *narrowed* the message rather than the commit that created the boundary. Note also
that one of the two is a **planned** test (private-symbol drift fallback, the fifth clause of the plan's
Phase-4 line) that had not landed when the plan called the file "5 regression tests" — at `61973f8d` the
file held 4.

#### 4. `744fd28d` — log-once sentinel + example fix — IN 0.0.7 — `correction` (both)

- **`_missing_symbol_logged` module sentinel** added; `apply()` flips it after the first
  `logger.info` so repeated `ready()` calls do not re-log. **Why (stated):** the docstring "claimed
  to log a 'single' INFO notice ... but the log fired on every call." Another shipped
  docstring promise the code did not keep. (This whole mechanism is retired at `48f9f65d` — see
  `### Contract flips`, flip 2.)
- **Non-callable example corrected** in `safe_wrap_connection_method`'s `Raises:` block:
  `connection.cursor` (a bound method — callable, so the example contradicted itself) ->
  `connection.cursor()` (the cursor object). **Why (stated):** the example was self-contradicting.

Test counts: `tests/test_django_patches.py` 10 -> 11 (adds
`test_apply_logs_missing_symbol_notice_only_once`).

#### 5. `e82df83d` — test-only — IN 0.0.7 — `correction` (coverage of a shipped branch)

Adds `test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict`, pinning
`_patch_is_installed()`'s `installed is None` branch. 11 -> 12 tests. No source change.

--- (everything below this line is genuinely post-tag-0.0.7) ---

#### 6. `52d97ec0` — cosmetic — POST — layout only

`tests/test_django_patches.py` only: one assertion re-wrapped across three lines for the
line-length-100 / trailing-comma layout rule. No assertion, name, or value changed. **Cosmetic
because** the diff is whitespace and parenthesisation of a single `assert` expression.

#### 7. `e145ba36` — subpackage rename `test` -> `testing` — POST — `serves-later-work`

**What:** `django_strawberry_framework/test/_wrap.py` -> `django_strawberry_framework/testing/_wrap.py`;
`tests/test/test_wrap.py` -> `tests/testing/test_wrap.py`; the public import path in every
docstring (`_django_patches.py`, `_wrap.py` module docstring, `_wrap.py` restoration-semantics code
block) rewritten to `django_strawberry_framework.testing`.
**Why:** the commit message is a bare `refactor: rename test subpackage to testing`. **Inference:**
`django_strawberry_framework.test` shadows the stdlib-adjacent name and collides with pytest's
collection of a package named `test`; the rename is package-wide, not 024-specific. Marked
inference — the message does not say.
**Contract impact:** the documented consumer import path changed. Any consumer following the 0.0.7
docstring's `from django_strawberry_framework.test import safe_wrap_connection_method` breaks. See
`### Contract flips`, flip 3.
**Classification:** `serves-later-work` — driven by a package-wide naming decision, not by a defect
in this surface.

#### 8. `b8a8a6e0` — `_wrap.py` docstring restructure — POST — cosmetic-plus

`safe_wrap_connection_method.__doc__`: the `Restoration semantics` RST subsection heading is
folded into a `**Restoration semantics.**` bold run (an RST subsection inside a docstring body was
the actual defect), and the example code block gains the missing
`from django.test import TransactionTestCase` import. **Cosmetic because** no executable line
changed; called out anyway because the example was previously non-runnable as written.

#### 9. `7cc163db` — ASCII-only sweep — POST — cosmetic, with one executable string

20 changed lines in `_django_patches.py` — 10 `-`/`+` pairs
(`diff -u /tmp/dsf-024-scratch/patches-e145ba36.py /tmp/dsf-024-scratch/patches-7cc163db.py |
grep -c '^[+-][^+-]'` -> 20) — all em-dash/arrow -> ASCII. **Cosmetic because** 9 of the 10 pairs
are docstring text. The tenth pair is executable: the `logger.info(...)` message literal
`"...skipping _remove_databases_failures patch — "` becomes `"... patch - "`. That string is
retired wholesale at `48f9f65d`, so nothing downstream depends on either spelling.

#### 10. `4a25bf42` — module-docstring first lines — POST — cosmetic

`_django_patches.py` first line -> `"""Defensive patches for upstream Django bugs, applied at app
load."""`; `testing/_wrap.py` first line -> `"""Cooperative connection-method wrapping for consumer
test instrumentation."""`. **Cosmetic because** only the summary line changed — but note both
strings are *rendered into* `docs/TREE.md` (lines 196, 278, 317, 403 carry them verbatim), so they
are generated-doc inputs, not free text.

#### 11. `7c2a63ed` — test module docstrings — POST — cosmetic

One summary line each in `tests/test_apps.py`, `tests/test_django_patches.py`,
`tests/testing/test_wrap.py`. Same TREE.md-input caveat (TREE.md lines 457, 549, 680, 775).

#### 12. `c7cb5f5c` — `APPLY_UPSTREAM_PATCHES` arrives — POST — `serves-later-work`

**What:** `_django_patches.py` imports `upstream_patches_enabled` from `.conf`; `apply()` gains
`if not upstream_patches_enabled(): return` as its **first** statement, ahead of the
missing-symbol branch. Module docstring gains the settings paragraph.
`apps.py::…ready` is rewritten from one applier to three
(`apply_django()`, `apply_strawberry()`, `apply_cross_web()`), with function-local imports.
**Why (stated):** the commit ships two NEW patch modules (`_strawberry_patches`,
`_cross_web_patches`) for a non-UTF-8 request-body 500, and — quoting the body — "All package
patches, including the existing Trac #37064 one, are now gated by a single
`DJANGO_STRAWBERRY_FRAMEWORK["APPLY_UPSTREAM_PATCHES"]` setting (default on; opt-out)."
**Classification:** `serves-later-work`, unambiguously — the driver is a Strawberry/cross_web bug
this card knows nothing about. The 024 surface is a passenger.
**Contract impact:** the 0.0.7 planning stance that the patch needs no settings key is superseded
— see `### Contract flips`, flip 4, and the answer to the dispatch's escape-hatch question below.

#### 13. `48f9f65d` — `_validate_upstream_shape` (2 tiers) + fail-loud — POST — `correction`

**What:**
- `_original_remove_databases_failures = SimpleTestCase.__dict__.get("_remove_databases_failures")`
  captured at module import.
- New `_validate_upstream_shape()` raising `RuntimeError` on (a) `_DatabaseFailure is None` OR the
  descriptor not a `classmethod` OR no `__func__`, and (b) the signature not being exactly one
  `POSITIONAL_OR_KEYWORD` parameter.
- `apply()` calls it after the settings gate and before `_patch_is_installed()`.
- **`logger`, `logger.info`, and `_missing_symbol_logged` all deleted.** The graceful-degradation
  branch is gone.
- Tests: `test_apply_no_ops_when_database_failure_symbol_missing` and
  `test_apply_logs_missing_symbol_notice_only_once` are **deleted**;
  `test_apply_fails_loudly_when_database_failure_symbol_missing` and
  `test_apply_fails_loudly_when_upstream_method_signature_changes` are added. **13 -> 13 tests** —
  re-measured in pass 2; pass 1 wrote "12 -> 13", which is wrong at both ends. The file already held 13
  before this commit (`c7cb5f5c` took 12 -> 13 by adding `test_apply_no_ops_when_toggle_disabled`), and
  this commit is net zero: two deleted, two added. That net-zero shape is exactly why the count was worth
  re-deriving — a `-2/+2` commit is invisible to a count-only record, and this is the commit where the
  graceful-degradation contract was retired.
**Why:** the commit message (`Refactor subsystem clear registration and handling`) is about the
type registry and **says nothing about this file**. **Inference** from the diff and from the
successor commit `0d655bde`'s body ("fail-loud upstream validation"): the package decided that
silently dropping a defensive patch is worse than refusing to boot, now that an explicit opt-out
exists (`c7cb5f5c` shipped it one commit earlier). Marked inference.
**Classification:** `correction` — it repairs a stance (silent degradation) the ship chose, and the
new stance is the one HEAD keeps.
**This is the largest flip in the cycle** — see `### Contract flips`, flip 2.

#### 14. `0d655bde` — body pin (3rd tier) + per-dependency opt-out — POST — `correction` + `serves-later-work`

**What (two separable changes in one commit):**
- **`correction`:** `import textwrap`; new
  `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` holding the verbatim dedented Django 5.2-6.0 body;
  `_validate_upstream_shape` gains a third tier comparing
  `textwrap.dedent(inspect.getsource(function))` against it, with `except (OSError, TypeError):
  source = None` so unreadable source (bytecode-only distribution) is treated as drift.
  **Why (stated):** "this module reimplements rather than delegates; shape-passing body drift now
  refuses to install instead of clobbering a working teardown." The ship's replacement silently
  superseded whatever upstream body was there — that is the defect.
- **`serves-later-work`:** `upstream_patches_enabled()` -> `upstream_patches_enabled("django")`,
  and all three drift `RuntimeError` messages change from
  `"Disable APPLY_UPSTREAM_PATCHES or use a supported Django version."` to
  `'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} or use a supported Django
  version.'` **Why (stated):** "All three apply() gates go through upstream_patches_enabled and
  every drift RuntimeError names the per-dependency escape hatch." Driven by the three-module
  patch family, not by this card.
- Tests 13 -> 17. The retirement test is switched to "drive the live import-time capture instead of
  a hardcoded 5.2.13 copy."

#### 15. `136c5476` — `ready()` dispatch test + docstring dedup — POST — `correction`

**What:** `tests/test_apps.py` gains `test_ready_dispatches_all_three_patch_appliers_and_refires_safely`;
`apps.py` module docstring and `ready()` docstring stop repeating each patch module's bug
inventory. **Why (stated):** "previously each module's installed-at-collection test was masked by
earlier idempotence tests on the same worker, so a dropped dispatch line could pass the gate." A
real gap in the gate, closed.

#### 16. `5a74d803` — cosmetic — POST

`tests/test_apps.py` and `tests/test_django_patches.py` comment/docstring text only: review
bookkeeping (`rev4 L4`, `rev-apps.md Medium 2, owned by rev-conf.md`) stripped from prose.
**Cosmetic because** no assertion, name, or value changed. Relevant to the spec only as evidence
that process provenance is banned from code comments.

#### 17. `eb2a1764` — the audited SET, and Django 6.1 — POST — `correction`

**What:**
- `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` (one string) becomes
  `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES: tuple[str, ...]` of **two** bodies; the third tier
  becomes `if source not in _AUDITED_…` and its message becomes "no longer matches any audited
  upstream body this patch supersedes."
- New helper `_disallowed_connection_methods(cls, connection)`, discriminating on
  `hasattr(cls, "_disallowed_connection_methods")`; `_patched_remove_databases_failures` calls it
  instead of reading `cls._disallowed_connection_methods` directly.
- The comment block gains the standing rule, verbatim: `WIDENING THIS SET IS AN AUDIT, NOT A
  VERSION BUMP`.
**Why (stated):** "Django 6.1 deleted `SimpleTestCase._disallowed_connection_methods` and moved the
same four `(name, operation)` pairs onto the per-connection feature flag
`disallowed_simple_test_case_connection_methods` ... The single pinned body matched neither shape,
so `AppConfig.ready()` raised and the package refused to boot on 6.1." The `0d655bde` pin was
correct-but-brittle by design; 6.1 is what made it fire.
**Classification:** `correction` of the pin's scope. Tests 17 -> 20; the message notes "Both
branches are driven synthetically, since whichever Django is installed leaves the other
unreachable" — which is exactly why the floor run in this pass matters (see
`### Floor verification`).

#### 18. `18550f5d` — reload-safe capture + discriminator change — POST — `correction` (both)

The commit is titled for an unrelated async-mutation mutex; its body's second paragraph says
"Review 0.0.14 also pins the transport boundaries it audited: ... patch reinstall survives module
reload." Two separable changes land here:

- **Reload-safe descriptor capture.** New `_PATCH_OWNER_ATTRIBUTE`
  (`"_django_strawberry_framework_patch_owner"`), `_PATCH_ORIGINAL_ATTRIBUTE`
  (`"_django_strawberry_framework_original"`), `_PATCH_OWNER`
  (`"django_strawberry_framework._django_patches"`), and
  `_captured_upstream_descriptor()`. The two owner attributes are stamped onto
  `_patched_remove_databases_failures` at module scope (two `setattr` calls after the function
  definition). `_original_remove_databases_failures = _captured_upstream_descriptor()` replaces the
  bare `SimpleTestCase.__dict__.get(...)`.
  **Why (stated in the docstring, which is the only statement):** `importlib.reload()` re-executes
  the module while `SimpleTestCase` still points at the previous replacement; reading that
  replacement as "the original" turns the next `ready()` into a false upstream-drift error. See
  "What breaks without it" below for the mechanical proof.
- **Discriminator change inside `_disallowed_connection_methods`.** `hasattr(cls,
  "_disallowed_connection_methods")` is replaced by an `==` comparison of a new module global
  `_validated_remove_databases_failures_source` against the two now-named constants
  `_CLASS_ATTRIBUTE_REMOVE_DATABASES_FAILURES_SOURCE` /
  `_CONNECTION_FEATURE_REMOVE_DATABASES_FAILURES_SOURCE`, with a **new fail-closed** `RuntimeError`
  ("ran without a validated upstream `_remove_databases_failures` body") when neither matches.
  `_validate_upstream_shape()` changes return type `None -> str` and `apply()` assigns its result
  to the new global before the install.
  **Why (stated in the rewritten docstring):** "Looking for the legacy attribute on `cls` is not
  equivalent: a Django 6.1 subclass may still declare one, but `_add_databases_failures` ignores it
  and wraps the feature list, so cleanup must read that same feature list to remain symmetric."
  The `eb2a1764` discriminator was wrong for exactly one case and it took two commits to find.
  Tests 20 -> 21 (`test_disallowed_methods_rejects_an_unvalidated_upstream_shape`).

#### 19. `f7fbead4` — `TypeError` message no longer interpolates the wrapper — POST — `correction`

**What:** `safe_wrap_connection_method`'s guard changes from
`f"safe_wrap_connection_method() received a non-callable wrapper: {wrapper!r}"` to
`"safe_wrap_connection_method() received a non-callable wrapper"`.
**Why (stated):** "the non-callable wrapper error no longer interpolates the object it is
complaining about" — the object is attacker/consumer-controlled and its `__repr__` can itself
raise, which would convert the intended `TypeError` into whatever the repr raises.
Pinned by `tests/testing/test_wrap.py::test_safe_wrap_connection_method_keeps_type_error_boundary_for_hostile_repr`.
7 tests at HEAD in that file.
**Classification:** `correction` of the guard shipped at `7014125a`.

#### 20. `36cd1925` — cosmetic — POST

`tests/test_apps.py` comment prose only; a stale "the spec-017 'no ready() body in 0.0.7' stance is
deliberately superseded" note is reworded to "``ready`` is deliberately absent from this set: it is
required on this class, not forbidden." No assertion changed.

---

### Contract flips

Every behavior the shipped code offered and HEAD no longer offers. Before-state quotes come from
the read-only blobs under `/tmp/dsf-024-scratch/`; after-state quotes from the working-tree file
(proven byte-identical to `18550f5d`'s blob).

#### Flip 1 — the patch installs on `TransactionTestCase`, then on `SimpleTestCase`

**Before** (`300e2811`, `apply()`), and this is what the tag-`0.0.7` docstring's `Currently
implemented` bullet still promised for four days:

```python
TransactionTestCase._remove_databases_failures = classmethod(
    _patched_remove_databases_failures,
)
```

**After** (HEAD, `apply()`):

```python
SimpleTestCase._remove_databases_failures = classmethod(
    _patched_remove_databases_failures,
)
```

**Retired claim:** "defensive replacement for
`django.test.testcases.TransactionTestCase._remove_databases_failures`". A direct `SimpleTestCase`
subclass was NOT covered at ship. Flipped inside the 0.0.7 release, at `7014125a`.

#### Flip 2 — a missing `_DatabaseFailure` goes: ImportError -> silent INFO no-op -> hard `RuntimeError`

Three states, not two. This is the flip the dispatch asked to be proven from source.

**State A** (`300e2811`, module scope) — no guard at all:

```python
from django.test.testcases import TransactionTestCase, _DatabaseFailure
```

If the symbol is absent the **module import raises `ImportError`**, and since
`apps.py::…ready` imports `apply` from it, Django's app registry population fails. The ship had no
handling for this case; the crash is incidental, not designed.

**State B** (`7014125a` + `744fd28d`, i.e. what tag `0.0.7` actually shipped) — graceful,
logged-once no-op:

```python
    global _missing_symbol_logged
    if _DatabaseFailure is None:
        if not _missing_symbol_logged:
            logger.info(
                "django-strawberry-framework: skipping _remove_databases_failures patch — "
                "Django's private _DatabaseFailure symbol is unavailable at this Django "
                "version. The Trac #37064 backstop will not be installed.",
            )
            _missing_symbol_logged = True
        return
```

Docstring promise at that point: "That keeps the rest of the package loadable on future Django
versions that break the private symbol."

**State C** (HEAD, via `48f9f65d`) — fail-closed. `logger`, `logger.info`, and
`_missing_symbol_logged` do not exist in the file
(`grep -n "logger\|_missing_symbol_logged" django_strawberry_framework/_django_patches.py` -> no
matches). `apply()` calls `_validate_upstream_shape()`, whose first tier is:

```python
    if _DatabaseFailure is None or not isinstance(descriptor, classmethod) or function is None:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: expected "
            "django.test.testcases._DatabaseFailure and "
            "SimpleTestCase._remove_databases_failures as a classmethod. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} '
            "or use a supported Django version.",
        )
```

**Retired claims (all three were true and are now false):** "keeps the rest of the package loadable
on future Django versions that break the private symbol"; "`apply()` will no-op instead of crashing
the whole app loader"; "logs a single INFO-level notice ... and returns without touching
`SimpleTestCase`." At HEAD a missing symbol means the app does not boot unless the consumer sets
`{"django": False}`. Two tests (`test_apply_no_ops_when_database_failure_symbol_missing`,
`test_apply_logs_missing_symbol_notice_only_once`) were deleted with the mechanism.

**Asymmetry worth stating in the spec:** `safe_wrap_connection_method` did NOT follow. Its symbol
-absent behavior is still degrade-and-install, pinned at HEAD by
`tests/testing/test_wrap.py::test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`
(`assert installed is True`). So the two halves diverge under private-symbol drift: the unwrap half
refuses to boot, the wrap half proceeds as if no Django wrapper were present. That path is only
reachable with the Django patch opted out, since otherwise `ready()` raises first.

#### Flip 3 — the documented consumer import path `…test` -> `…testing`

**Before** (`61973f8d`, `_wrap.py` restoration-semantics code block):

```python
from django_strawberry_framework.test import safe_wrap_connection_method
```

**After** (HEAD): `from django_strawberry_framework.testing import safe_wrap_connection_method`.
`django_strawberry_framework/testing/__init__.py` re-exports the name in `__all__`;
`django_strawberry_framework/__init__.py` does not mention it (grep -> no matches), so the helper
is submodule-path-only at HEAD, as it was at ship. Flipped at `e145ba36`, post-tag.

#### Flip 4 — "no settings key required" -> gated by `APPLY_UPSTREAM_PATCHES`

**Before** (`300e2811` module docstring, unchanged through tag `0.0.7`):

> consumers get them automatically by having `"django_strawberry_framework"` in `INSTALLED_APPS` —
> no opt-in boilerplate (no `conftest.py` workaround, no test-case base class to inherit) is
> required on the consumer side.

No settings read of any kind existed in the file.

**After** (HEAD, `apply()` first statement): `if not upstream_patches_enabled("django"): return`,
with the module docstring naming both the global `False` and the per-dependency
`{"APPLY_UPSTREAM_PATCHES": {"django": False}}` forms.

**Retired claim:** the 0.0.7 stance that the hardening is unconditional. It is now conditional, and
the condition can be set to skip it. The "no opt-in boilerplate" half survives (the default is on);
the "unconditional" half does not. Arrived in two steps — global bool at `c7cb5f5c`, per-dependency
mapping at `0d655bde`.

#### Flip 5 — the replacement supersedes ANY upstream body -> only an audited one

**Before** (`300e2811` .. `48f9f65d`): `apply()` installed the replacement without ever reading
upstream's body. The docstring's claim — "Identical to Django's upstream classmethod except for the
`isinstance(...)` guard" — was asserted, never checked.

**After** (HEAD, `_validate_upstream_shape` third tier):

```python
    if source not in _AUDITED_REMOVE_DATABASES_FAILURES_SOURCES:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: "
            "SimpleTestCase._remove_databases_failures no longer matches any audited "
            "upstream body this patch supersedes. "
            ...
```

**Retired claim:** that the patch is safe on any Django. It is safe on exactly the Django versions
whose body text is one of the two audited strings, and refuses to install (and therefore refuses to
boot) on every other. Two steps: single pin `0d655bde`, set-of-two `eb2a1764`.

#### Flip 6 — `_disallowed_connection_methods` discriminator: `hasattr(cls, …)` -> validated body

**Before** (`eb2a1764`):

```python
    if hasattr(cls, "_disallowed_connection_methods"):
        return cls._disallowed_connection_methods
    return connection.features.disallowed_simple_test_case_connection_methods
```

with the docstring claiming "The presence of the class attribute is therefore the discriminator,
read off `cls` rather than off a Django version number so a subclass that still declares its own
list keeps being honoured."

**After** (HEAD): the discriminator is `_validated_remove_databases_failures_source` compared `==`
against the two named body constants, with a fail-closed `RuntimeError` when neither matches, and
the docstring's claim **inverted**:

> Looking for the legacy attribute on `cls` is not equivalent: a Django 6.1 subclass may still
> declare one, but `_add_databases_failures` ignores it and wraps the feature list, so cleanup must
> read that same feature list to remain symmetric.

**Retired claim:** "a subclass that still declares its own list keeps being honoured" was stated as
a feature at `eb2a1764` and is named as a **bug** at `18550f5d`. It lived 10 days
(2026-08-06 -> 2026-08-16). This is the flip most likely to be re-introduced by a well-meaning
reader, because the `hasattr` form looks more robust than the global.

#### Flip 7 — `_PATCH_APPLIED` bool -> `_patch_is_installed()` identity check

**Before** (`300e2811`):

```python
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return
```

**After** (HEAD): `if _patch_is_installed(): return`, where `_patch_is_installed` compares
`SimpleTestCase.__dict__.get("_remove_databases_failures").__func__` identity against
`_patched_remove_databases_failures`.

**Retired claim:** the ship's own docstring, "Idempotent: re-entrant calls are no-ops" — true, but
it silently also meant "and never re-installs after a third party reverts." HEAD's promise is
"idempotent **and self-healing**." Flipped at `7014125a`, inside the release.

#### Flip 8 — `TypeError` text no longer names the offending object

**Before** (`7014125a` .. `4a25bf42`):

```python
        raise TypeError(
            f"safe_wrap_connection_method() received a non-callable wrapper: {wrapper!r}",
        )
```

**After** (HEAD): the same `raise TypeError` with the literal
`"safe_wrap_connection_method() received a non-callable wrapper"` and no interpolation.

**Retired claim:** the diagnostic named the object. A consumer parsing that message, or relying on
the repr to identify which argument was wrong, gets less at HEAD — deliberately, because a hostile
`__repr__` could replace the `TypeError` with an arbitrary exception. Flipped at `f7fbead4`.

#### What breaks without the reload-safe descriptor capture (flip 2's sibling, asked explicitly)

Mechanically proven, read-only, in the shared `.venv`:

```shell
uv run python /tmp/dsf-024-scratch/probe.py
#   installed descriptor func is patch: True
#   owner attr on patch func: django_strawberry_framework._django_patches
#   patch own source in audited set: False
#   _captured_upstream_descriptor() returns the ORIGINAL (not the patch): True
```

Chain: after `apply()`, `SimpleTestCase.__dict__["_remove_databases_failures"].__func__` **is**
`_patched_remove_databases_failures` (row 1). `importlib.reload(_django_patches)` re-executes the
module while that installation stands. Without `_captured_upstream_descriptor`,
`_original_remove_databases_failures` would therefore be the package's own replacement, and
`_validate_upstream_shape`'s third tier would compute
`textwrap.dedent(inspect.getsource(_patched_remove_databases_failures))`, which is **not** in the
audited set (row 3). The next `apply()` — i.e. the next `ready()` — would raise
`RuntimeError("… no longer matches any audited upstream body this patch supersedes")` against the
package's own code. The owner stamp (row 2) is what breaks the chain, letting
`_captured_upstream_descriptor()` recover the true Django descriptor (row 4).
Pinned by `tests/test_apps.py::test_ready_reinstalls_patches_after_their_modules_reload`, which
reloads each patch module **twice** so the contract holds for a reload of a reload.

#### What the audited-body pin costs (asked explicitly)

`_validate_upstream_shape` pins the **exact dedented source text** of
`SimpleTestCase._remove_databases_failures` — not its behavior, not its signature (that is tier 2),
not a version range. Consequences, each provable from the file:

- **Any** upstream edit to that body — including a comment, a rename of a local, a reflow, or an
  upstream fix of Trac #37064 itself — fails the `not in` check and raises at `ready()`. A Django
  patch release that reflows the method bricks the consumer's app boot until they set
  `{"django": False}`.
- The pin is what makes the reimplement-instead-of-delegate design safe, and the file says so:
  the sibling patches (`_cross_web_patches` / `_strawberry_patches`) delegate, so "upstream body
  changes flow through the delegated call" and they need only their call shape validated.
- `WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP` (the comment's own capitals) means adding a
  third string is not sufficient: the comment requires that "a new upstream body joins the set only
  after its read path is reimplemented in `_disallowed_connection_methods` and Trac #37064's crash
  shape is re-confirmed against it." That is a three-part obligation — new string, new read branch,
  re-confirmed crash — and `eb2a1764` -> `18550f5d` is the proof that getting the read branch wrong
  is easy: the first attempt at the read branch shipped and was corrected 10 days later.
- The audited set has exactly **2** members at HEAD
  (`_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES = (_CLASS_ATTRIBUTE_…, _CONNECTION_FEATURE_…)`),
  covering the claimed range 5.2.16 - 6.1.

---

### Validation run

- `uv run ruff format <files this pass touched>` — **not run**: this pass touched no `.py` file.
  Ruff's write mode is not run on Markdown.
- `uv run ruff check --fix <the same files>` — **not run**, same reason.
- `git status --short` after the pass — the only new entry attributable to this pass is
  `?? docs/builder/bld-slice-1b-024-divergence_and_floor.md`. Everything else present
  (`CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/feedback.md`,
  `examples/fakeshop/db.sqlite3`, the spec-021/022/023 files, every `docs/builder/*-023*.md`, the
  `docs/builder/DONE/build-02*.md` additions, the four staged deletions under `docs/builder/`, and
  `docs/builder/build-024-…md`) is on the build plan's baseline-dirty list or is the build plan
  itself. `docs/builder/worker-memory/worker-2-024.md` is gitignored and does not appear.
  No unexpected churn; nothing reverted.
- Focused test commands: recorded under `### Floor verification` below (both were run without any
  `--cov*` flag; `--no-cov` supplied because `pytest.ini` `addopts` auto-applies `--cov`).

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Owned by this pass per the build plan's `**Floor-verification scope:**` declaration.

**Floor venv (outside the repo):** `/tmp/dsf-floor-024`. The shared `.venv` was never installed
into; every `uv pip install` carried an explicit `--python /tmp/dsf-floor-024/bin/python`.

```shell
uv venv /tmp/dsf-floor-024 --python 3.10
uv pip install --python /tmp/dsf-floor-024/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor-024/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'
```

All three exited 0. The third step's own output records what it displaced:
`- django==5.2.17 / + django==5.2.16` and `- strawberry-graphql==0.324.0 / + strawberry-graphql==0.316.0`
— i.e. `-e . --group dev` alone resolves ABOVE the floor on both, so the explicit pin is doing real
work.

**Resolved versions, as read (not from memory):**

`uv pip list --python /tmp/dsf-floor-024/bin/python` and `/tmp/dsf-floor-024/bin/python -V`:

| package | floor venv | shared `.venv` |
|---|---|---|
| python | 3.10.19 | 3.14.2 |
| django | 5.2.16 | 6.1 |
| strawberry-graphql | 0.316.0 | 0.323.2 |
| channels | 4.3.2 | 4.3.2 |
| asgiref | 3.12.1 | 3.11.1 |
| pytest | 9.1.1 | 9.0.3 |

Shared-env rows read with `uv pip list` and `.venv/bin/python -V` in the same pass. **The two
environments do NOT agree** on python, django, strawberry-graphql, asgiref, or pytest — only
`channels` matches. That is expected (the shared env tracks the newest supported versions) and it
is precisely what makes this run load-bearing: see the discriminator result below.

**Focused scope, floor:**

```shell
/tmp/dsf-floor-024/bin/python -m pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov
#   ============================== 36 passed in 1.12s ==============================
```

**PASS**, exit 0. No failures, no errors, no skips reported.

**Same scope, shared `.venv`:**

```shell
uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov
#   ============================== 36 passed in 1.52s ==============================
```

**PASS**, exit 0. 36 in both environments, and 36 is the sum of the three files' test-function
counts: 21 + 7 + 8 (`grep -c '^def test_'` on each).

**The result the floor run exists to produce.** The two environments resolve the body pin to
*different* audited bodies, so each environment executes a branch the other cannot reach. Probe
(`/tmp/dsf-024-scratch/probe2.py`, read-only, `django.setup()` then read module globals):

| | floor (django 5.2.16) | shared (django 6.1) |
|---|---|---|
| `_validated_remove_databases_failures_source == _CLASS_ATTRIBUTE_…` | **True** | False |
| `_validated_remove_databases_failures_source == _CONNECTION_FEATURE_…` | False | **True** |
| `hasattr(SimpleTestCase, "_disallowed_connection_methods")` | True | **False** |
| `hasattr(connection.features, "disallowed_simple_test_case_connection_methods")` | False | **True** |
| `_disallowed_connection_methods(SimpleTestCase, connection)` | 4 pairs | 4 pairs |

Both resolve to the identical four pairs:
`(('connect', 'connections'), ('temporary_connection', 'connections'), ('cursor', 'queries'),
('chunked_cursor', 'queries'))`.

So the class-attribute audited body — the one covering `5.2.16-6.0.x`, i.e. most of the supported
range — is executed **only** at the floor. In the shared `.venv` that branch is reachable only
synthetically, which is exactly what `eb2a1764`'s commit message admitted ("Both branches are
driven synthetically, since whichever Django is installed leaves the other unreachable"). Before
this run, the 5.2.16 claim was a claim. It now has one executed point in it.

### Implementation notes

- Chronology was re-derived from `%cd` on every commit rather than trusted from the dispatch's
  ordering, after the `e145ba36` diff read backwards. Every diff in the catalog is taken in
  commit-date order.
- Every count in this artifact was produced by a command at the moment it was written: commit
  counts by `git log --oneline --follow -- <path> | wc -l`, test counts by
  `grep -c '^def test_'` on the extracted blob, changed-line counts by
  `diff -u … | grep -c '^[+-][^+-]'`. The `36` in both test runs is pytest's own summary line, and
  it reconciles with 21 + 7 + 8.
- The `is` vs `==` distinction bit once during probing: `_validated_remove_databases_failures_source`
  holds a *fresh* string from `textwrap.dedent(inspect.getsource(...))`, so an identity comparison
  against the module constants reports False in both environments while the code's own `==`
  comparison reports True. The first probe used `is` and produced a false "neither shape matched"
  reading; the table above is from the corrected `==` probe. Anyone re-deriving this must use `==`.
- Scratch lives at `/tmp/dsf-024-scratch/` (blobs, two probe scripts) and `/tmp/dsf-floor-024`
  (venv), both outside the repo. `docs/builder/temp-tests/` was created but left empty.

### Notes for Worker 3

- Nothing to review in source; the diff for this pass is one new Markdown file.
- Every quoted before-state is reproducible with
  `git show <rev>:django_strawberry_framework/_django_patches.py`; the after-states are the
  working-tree file, which `diff -u` proves byte-identical to `18550f5d`'s blob.
- `scripts/review_inspect.py` was not run; the build plan's pre-flight already ran it on
  `_django_patches.py` and this pass needed line-level history, not a static overview.

### Notes for Worker 1 (spec reconciliation)

Worker 1 writes the contract from this section. Facts the rewritten spec MUST state, and
explanations the rationale companion MUST carry.

**Facts for the spec (current contract at HEAD, stated without history):**

1. The patch installs on `django.test.testcases.SimpleTestCase._remove_databases_failures` — the
   definition site — so `TransactionTestCase` and `TestCase` inherit it through the MRO. Not
   `TransactionTestCase`.
2. `apply()` is gated by `APPLY_UPSTREAM_PATCHES` (default on), read through
   `django_strawberry_framework.conf.upstream_patches_enabled("django")`, and accepts a global
   bool or a per-dependency mapping over `UPSTREAM_PATCH_DEPENDENCIES`
   (`frozenset({"django", "strawberry", "cross_web"})`). The gate is `apply()`'s **first**
   statement, ahead of all validation, so `{"django": False}` silences a drifted-pin abort.
3. `_validate_upstream_shape()` is three tiers and every tier raises `RuntimeError` naming the
   per-dependency escape hatch: (a) `_DatabaseFailure` present AND the descriptor is a
   `classmethod` with a `__func__`; (b) exactly one `POSITIONAL_OR_KEYWORD` parameter; (c) the
   dedented source of the captured original is a member of
   `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` — 2 bodies, class-attribute (5.2.16-6.0.x) and
   connection-feature (6.1). Unreadable source (`OSError`/`TypeError` from `inspect.getsource`)
   is drift, not an exemption.
4. A missing `_DatabaseFailure` is a **hard failure at app load**, not a degradation. State this
   explicitly; the ship's opposite promise is still quotable from git.
5. `_disallowed_connection_methods(cls, connection)` discriminates on the **validated body**, not
   on `hasattr(cls, …)`, and raises `RuntimeError` when no body has been validated. The spec should
   carry the reason inline as a contract statement, not as history: `_add_databases_failures`
   ignores a 6.1 subclass's legacy attribute and wraps the feature list, so cleanup must read the
   feature list to stay symmetric.
6. Reload safety is part of the contract: `_patched_remove_databases_failures` carries two stamped
   attributes (`_django_strawberry_framework_patch_owner`,
   `_django_strawberry_framework_original`) and `_captured_upstream_descriptor()` reads through
   them, so `importlib.reload()` of the patch module recovers Django's true descriptor instead of
   re-validating the package's own function.
7. `apply()` is idempotent **and self-healing** via `_patch_is_installed()` identity comparison;
   `ready()` may fire more than once.
8. `safe_wrap_connection_method` lives at `django_strawberry_framework.testing`
   (submodule path only — not re-exported from the package root), raises `TypeError` on a
   non-callable wrapper **without interpolating the wrapper**, and on a missing `_DatabaseFailure`
   installs (returns `True`) rather than failing — the deliberate asymmetry with `apply()`.
9. `apps.py::…ready` dispatches three appliers in order: `_django_patches`, `_strawberry_patches`,
   `_cross_web_patches`, behind function-local imports; the inventory of what each hardens lives in
   each module's docstring and `ready()` deliberately repeats none of it.

**Explanations for the rationale companion:**

- The `WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP` rule, its three-part obligation, and the
  `eb2a1764` -> `18550f5d` evidence that the read-branch half is the one that goes wrong.
- Why reimplement rather than delegate, and why that choice is what forces the body pin (the
  file's own contrast with the delegating siblings).
- The debug-toolbar precedent, both halves: the SQL panel's wrap-time isinstance (the pattern
  mirrored) and the cache-panel's owner-sentinel conclusion (the pattern NOT available here,
  because the package does not own Django's wrapper).
- Every entry in `### Contract flips` above, as "claims this decision may no longer make." Flip 6
  is the highest-value one: the `hasattr` discriminator was documented as a feature and is now
  documented as a bug, so a future reader who "simplifies" it back reintroduces a known defect.
- The three-state history of flip 2 (incidental ImportError -> designed silent no-op -> designed
  hard failure), with the note that the middle state's two tests were deleted, not renamed.

**Escalated (needs Worker 1's decision, not mine):**

- **[DECISION — Worker 1's, as spec custodian] Where the rationale's change record starts.** The two
  cohorts hand Worker 1 opposite defaults, and neither could see the conflict from inside its own angle.
  This artifact catalogues `7014125a` as four ship **corrections** and raises two of them as contract
  flips (flip 1 `TransactionTestCase` -> `SimpleTestCase`, flip 7 `_PATCH_APPLIED` ->
  `_patch_is_installed`) with retired claims the rationale must carry. Slice 1a treats that same commit
  as the recovered plan's **baseline** — the plan post-dates it, so its changes are not divergences at
  all. Both readings are internally sound; they are opposite answers to "where does the change record
  begin", and `docs/builder/BUILD.md` `## Spec reconciliation` makes that the custodian's call, not a
  builder's. Recorded with evidence, not resolved.

  **The deciding fact, measured in pass 2 — the plan's upper bound, which neither cohort had.** It is not
  a window; it is a point:

  ```shell
  git log --format='%h %cI %s' --follow -- docs/PLAN-trac-37064-database-teardown.md
  #   d1d19ca2 2026-05-27T20:16 (deletes it)  df547235 2026-05-27T18:58  974189ad 2026-05-26T19:34
  #   7014125a 2026-05-26T10:21  61973f8d 2026-05-23T18:32  300e2811 2026-05-23T10:42
  git log --format='%h %cI' --follow -- docs/TEMP-trac-37064-test-plan.md   # d1d19ca2, 7014125a
  diff <PLAN at 7014125a> <PLAN at d1d19ca2^>    # exactly 2 lines
  diff <TEMP at 7014125a> <TEMP at d1d19ca2^>    # identical
  ```

  `TEMP-024.md` as recovered is byte-identical to its `7014125a` blob. `PLAN-024.md` as recovered differs
  from its `7014125a` blob by exactly two lines, both mechanical reference rewrites carrying no contract
  (`AGENTS.md line 20` -> the symbol-qualified form at `df547235`; a `SPECS/` path prefix at `974189ad`).
  So both documents describe the tree as of `7014125a` and describe nothing after it — including
  `744fd28d` (2026-05-26T15:09) and `e82df83d` (2026-05-26T15:27), both of which land after the plan's
  last content-bearing write with no plan update.

  **Consequence for this artifact's own flip 2.** Flip 2 calls state B "what tag `0.0.7` actually
  shipped", which is true, but the log-once **sentinel** in it was never in the *planned* contract: the
  plan and `TEMP-024.md` promise the missing-symbol no-op with one log notice, which is `7014125a`'s
  state — where the docstring claimed "a single INFO-level notice" while `apply()` called `logger.info`
  on every call. `744fd28d` added the sentinel to make the existing claim true. Whichever start point is
  chosen, the rationale should not describe the sentinel as a planned deliverable.

  **What each option costs.** (a) Start at `300e2811`: `7014125a` and `744fd28d` are in-release
  corrections with their own retired claims — this artifact's shape, and the one that survives this
  artifact's measured in-tag correction, at the cost of opening the record with four days of churn the
  plan never saw. (b) Start at the plan's baseline: flips 1 and 7 must then be stated as "the plan
  already describes the corrected form" rather than omitted, or the record silently loses two contract
  flips that a reader of the *ship* would still hit.

- **The dispatch's premise that all 13 commits are post-ship is false** (6 of the 21 surface
  commits are inside tag `0.0.7`). If Worker 1's plan text or the Slice 2 dispatch repeats the
  premise, it needs correcting before the rationale companion's change record is written from it.
- **`docs/GLOSSARY.md` `## Django Trac #37064 hardening` is stale against HEAD.** It says
  "no `conftest.py` workaround, no base test class to inherit, **no settings key required**" and
  describes the patch as unconditional. `APPLY_UPSTREAM_PATCHES`, the audited-body pin, and the
  fail-loud `RuntimeError` are absent from it. The glossary is out of scope for this cycle
  (build plan `## Cycle type and scope`), so this belongs in the deferred-work catalog, not in a
  fix.
- **`docs/TREE.md` is an unstated consumer of two module summary lines** changed by `4a25bf42` and
  `7c2a63ed` (TREE.md lines 196, 278, 317, 403, 457, 549, 680, 775). Worth one sentence in the spec
  so a future docstring edit knows it must be followed by a regenerate.
  **Citation form: those raw `path:NN` line numbers are non-transferable.** They are legal here —
  `START.md` "Temp artifact conventions" exempts `bld-*.md` scratchpads — and they are the right form
  for a reviewer re-deriving this. They must **not** be carried into the spec or the rationale, where
  `AGENTS.md` requires `path::QualifiedName` / `path #"unique substring"`. The sentence the spec should
  carry is "the two module summary lines are rendered into `docs/TREE.md`", with no numbers in it.

**The deferred-work catalog is the union of both cohorts' lists — this one is not the whole of it.**
Stated explicitly because the two lists are near-disjoint (they overlap only on `docs/GLOSSARY.md`) and a
final gate that takes either as complete drops half the catalog. This cohort's angle is the commit
history, so it cannot surface a defect that lives in a document and in no commit. Specifically, 1a
independently found that `CHANGELOG.md`'s shipped `## [0.0.7]` -> `### Added` entry carries two claims
that are false at HEAD ("no settings key"; "a log-once sentinel suppresses repeated missing-symbol
notices") and landed under `### Added` where the plan's DoD item 9 asked for `### Fixed`; and that
`django_strawberry_framework/_strawberry_patches.py` cited a constant renamed away at `eb2a1764` — 1
occurrence at HEAD, whose repair appears to have already landed uncommitted in the working tree under the
concurrent Slice 3 cohort, so it must be re-measured before it is homed. Neither appears in this
cohort's list above.

**No code gap found by this cohort.** Nothing in the post-ship history removed a capability the
0.0.7 contract promised without replacing it with a stated stronger one. Every flip is a deliberate
narrowing or hardening with a test pinning the new state. Slice 1a owns the independent
planned-vs-HEAD verdict; the two were not compared.

---

## Review (Worker 3)

Read-only review pass over Slice 1b's claims. No production diff exists in this slice, so the subject
is whether the artifact's statements are true — in particular the floor run, which is the one thing
in this cycle that cannot be re-derived from reading. Commands are quoted so the next reader
re-derives rather than accepts.

### Sample declaration: what I re-derived, and what I accepted unchecked

**Re-derived — every one reproduced exactly, unless a finding says otherwise:**

| Claim | Command | Result |
|---|---|---|
| six `--follow` commit counts 13 / 8 / 8 / 13 / 7 / 9 | `git log --oneline --follow -- <path> \| wc -l` on each of the six | **13, 8, 8, 13, 7, 9** |
| union 23, surface 21 | `for f in <six>; do git log --format=%h --follow -- $f; done \| sort -u \| wc -l` | **23**; minus `b972cd84` / `dfa035b4` (2026-05-21, pre-patch) = **21** |
| tag `0.0.7` -> `72f6cd9b` / `e2765ff3…` | `git rev-parse 0.0.7`; `git log -1 --date=short 0.0.7` | **`e2765ff31f63e35a3eeace026c5ab7ac70a40aae`**, `72f6cd9b 2026-05-27` |
| tag blob == `744fd28d` blob | `git show 0.0.7:…_django_patches.py` / `git show 744fd28d:…` then `diff -q` | **identical** |
| "five of the thirteen … are INSIDE the release" | `merge-base --is-ancestor <h> 0.0.7` over the 13-commit file history | **exactly 5**: `300e2811`, `893465a5`, `61973f8d`, `7014125a`, `744fd28d` |
| the 6 / 15 in-tag / post-tag split of the 21 | `merge-base --is-ancestor` per commit | **6 / 15**, membership as listed |
| the chronology correction (`e145ba36` -> `7cc163db` -> `4a25bf42`) | `git log -1 --format=%cd --date=short` on each | 2026-06-01 -> 2026-06-10 -> 2026-06-12; **correction confirmed** |
| test-count progression 6 -> 10 -> 11 -> 12 -> 13 -> 17 -> 20 -> 21 | `git show "<h>:tests/test_django_patches.py" \| grep -c '^def test_'` per commit | **6, 10, 11, 12, 13, 17, 17, 20, 21** across `300e2811`, `7014125a`, `744fd28d`, `e82df83d`, `48f9f65d`, `0d655bde`, `136c5476`, `eb2a1764`, `18550f5d` — every stated number reproduces |
| `_wrap.py` test counts | same, on `tests/test/test_wrap.py` then `tests/testing/test_wrap.py` | **4 at `61973f8d`, 6 at `7014125a`**, 6 at `e145ba36`, **7 at `f7fbead4`** — one stated number does **not** reproduce, see M1 |
| flip 2 / flip 5 / flip 6 after-states | read `django_strawberry_framework/_django_patches.py` end to end | `_validate_upstream_shape`'s three tiers, the `except (OSError, TypeError)` drift arm, the `_validated_remove_databases_failures_source` `==` discriminator, and its fail-closed `RuntimeError` are all present as quoted; `grep -c logger` -> **0** |
| every commit hash cited by this artifact | `git log -1 <h>` + `merge-base --is-ancestor <h> HEAD` | **all 21 resolve and all are HEAD ancestors** — no dead citation in this artifact |
| no source touched | `git status --short \| grep '\.py$'` | one entry, `_strawberry_patches.py`, owned by the concurrent repair cohort |
| public-surface check | `git diff HEAD -- django_strawberry_framework/__init__.py` | **empty** |

**Accepted unchecked (named, so the sample is honest):** the per-commit `diff -u … | grep -c '^[+-][^+-]'`
changed-line counts in entries 9 and 11; the `docs/TREE.md` line numbers in the third escalation; the
prose classification (`correction` vs `serves-later-work`) of the cosmetic entries 6, 8, 10, 11, 16,
20; the two commit-message quotations I did not open the commit body for (`c7cb5f5c`, `18550f5d`).

### Floor verification audit

This is the part of the cycle that only execution can establish, so I re-executed all of it rather
than reading the record.

**Floor versions against the canonical statement.** `docs/builder/BUILD.md` `## Floor verification`
states the floor as Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. The
artifact's declared floor matches that statement exactly, and matches nothing taken from memory or
from another document.

**The venv still exists and resolves what the artifact recorded.**

```shell
/tmp/dsf-floor-024/bin/python -V                                  # Python 3.10.19
uv pip list --python /tmp/dsf-floor-024/bin/python | grep -Ei '^(django|strawberry-graphql|channels|asgiref|pytest) '
#   asgiref 3.12.1 / channels 4.3.2 / django 5.2.16 / pytest 9.1.1 / strawberry-graphql 0.316.0
uv pip list | grep -Ei '^(django|strawberry-graphql|channels|asgiref|pytest) '   # shared .venv
#   asgiref 3.11.1 / channels 4.3.2 / django 6.1 / pytest 9.0.3 / strawberry-graphql 0.323.2
.venv/bin/python -V                                               # Python 3.14.2
```

**Every one of the twelve version cells in the artifact's table reproduces**, including the
`channels`-is-the-only-match observation. No `uv pip install` was issued in this pass, so the shared
`.venv` was not mutated.

**Focused scope re-run at the floor.**

```shell
/tmp/dsf-floor-024/bin/python -m pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov -q
#   36 passed in 1.10s
```

**PASS**, exit 0, no skips. 36 also reconciles with 21 + 7 + 8 def-lines *and* with pytest's own
`--collect-only` node-id count, so the number is not a def-line artifact.

**The load-bearing claim — the two environments resolve the body pin to different audited bodies —
re-derived with my own probe**, not 1b's (`docs/builder/temp-tests/024-review/probe_discriminator.py`,
gitignored, `django.setup()` then read module globals after `apply()`):

| | floor (py 3.10.19 / django 5.2.16) | shared (py 3.14.2 / django 6.1) |
|---|---|---|
| `== _CLASS_ATTRIBUTE_REMOVE_DATABASES_FAILURES_SOURCE` | **True** | False |
| `== _CONNECTION_FEATURE_REMOVE_DATABASES_FAILURES_SOURCE` | False | **True** |
| `hasattr(SimpleTestCase, "_disallowed_connection_methods")` | True | **False** |
| `hasattr(connection.features, "disallowed_simple_test_case_connection_methods")` | False | **True** |
| `_disallowed_connection_methods(SimpleTestCase, connection)` | 4 pairs | 4 pairs |
| `len(_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES)` | 2 | 2 |

Both resolve to the identical four `(name, operation)` pairs. **Every cell matches the artifact's
table.** The claim that the class-attribute body — the shape covering most of the supported range —
executes *only* at the floor is confirmed, and the artifact's `is`-vs-`==` warning is correct and
worth keeping: an identity comparison reports `False` in both environments because
`textwrap.dedent(inspect.getsource(...))` returns a fresh string.

The floor run is accepted in full. It is the strongest single piece of evidence in this cycle and
none of my findings touch it.

### High:

None.

### Medium:

#### M1 — A stated test count that does not reproduce, in the entry whose own bullet contradicts it

Entry 3 (`7014125a`) closes: "Test count `tests/test_django_patches.py` 6 -> 10; `_wrap.py` **4 tests
unchanged in count**." Measured:

```shell
git show "61973f8d:tests/test/test_wrap.py" | grep -c '^def test_'   # 4
git show "7014125a:tests/test/test_wrap.py" | grep -c '^def test_'   # 6
```

The wrap test file goes **4 -> 6** at `7014125a`. The entry's own third and fourth bullets are why —
the guarded-import/`_is_database_failure` change and the `safe_wrap_connection_method` callable guard
each landed with a test. The 6 -> 10 half of the same sentence reproduces exactly, which is what makes
this the dangerous shape: a measured number sitting beside an unmeasured one in a single clause reads
as equally measured.

It matters beyond arithmetic. HEAD's 7 wrap tests decompose as 5 planned + 2 beyond-plan; with this
sentence, the two beyond-plan tests appear to have arrived at `f7fbead4` alone, and the rationale's
change record would attribute the `TypeError` boundary's coverage to the wrong commit. The correct
decomposition is: 4 at `61973f8d`, +2 at `7014125a` (private-symbol drift fallback, non-callable
`TypeError`), +1 at `f7fbead4` (hostile-`__repr__`) = 7.
**Fix:** state `_wrap.py` 4 -> 6 at `7014125a`, and 6 -> 7 at `f7fbead4` (which entry 19 already
implies with its correct "7 tests at HEAD").

### Low:

#### L1 — Two correct populations stated adjacently read as a contradiction

"**Five of the thirteen listed commits are INSIDE the 0.0.7 release**" sits directly above a table
headed "In tag `0.0.7` (**6**)". Both numbers are right about different populations — 5 of the
dispatch's 13 (the `_django_patches.py` file history), 6 of the 21-commit surface — and I reproduced
both. But the sentence is the correction's headline and the table is its evidence, so a reader who
re-derives either one against the other concludes the correction is wrong. Name the population in
each: "five of the dispatch's thirteen", "six of the twenty-one surface commits".

#### L2 — The deferred-work escalations omit `CHANGELOG.md`

The escalations carry `docs/GLOSSARY.md` and `docs/TREE.md`. Slice 1a independently found that the
shipped `## [0.0.7]` -> `### Added` entry carries two claims that are false at HEAD ("no settings key";
"a log-once sentinel suppresses repeated missing-symbol notices") and landed under `### Added` where
the plan's DoD item 9 asked for `### Fixed`. Nothing in 1b's angle would surface it — the entry is a
document, not a commit — but Worker 1 assembles one catalog from both artifacts, so say explicitly
that this cohort's list is not the whole catalog.

#### L3 — Two escalations use a citation form the spec cannot inherit

The `docs/TREE.md` escalation cites lines 196, 278, 317, 403, 457, 549, 680, 775. Raw `path:NN` is
legal inside a `bld-*.md` per `START.md` "Temp artifact conventions", and it is the right form here.
Flag it as non-transferable so it is not carried into the spec or rationale, where `AGENTS.md`
requires `path::QualifiedName` / `path #"unique substring"`. Same for the sentence the escalation
asks the spec to carry: state it as "the two module summary lines are rendered into `docs/TREE.md`",
not as line numbers.

### Cross-cohort check against Slice 1a

The two cohorts were produced independently and never read each other. Where they touch the same
fact:

- **Agree — the load-bearing verdict.** Both return no code gap. I re-derived it independently,
  working from the recovered planned list inward, and **concur**.
- **Disagree — `e82df83d`'s test number.** 1b §5: "11 -> 12 tests". 1a: "(11th test)". Measured, **1b
  is right**; 1a's number is off by one because its table omits `744fd28d` (10 -> 11).
- **Disagree — the commit population.** 1a's 13-row table shares only 8 members with the 13-commit
  `_django_patches.py` history and contains **two commits that are ancestors of no ref**
  (`8e86e777`, `e69ff4f9` — patch-identical pre-rewrite duplicates of `0d655bde` and `136c5476`).
  Every hash in **this** artifact resolves and is a HEAD ancestor. **1b is right**, and its
  "Correction to the dispatch's own framing" section is vindicated more strongly than it claims: the
  dispatch's population was not merely incomplete, it was contaminated.
- **Disagree — the fail-loud attribution.** 1b splits it correctly: `48f9f65d` (tiers 1-2, `logger`
  and `_missing_symbol_logged` deleted, both retired tests deleted) then `0d655bde` (tier 3 body pin,
  per-dependency messages). 1a collapses both into one dead hash. I confirmed the split with
  `git log -S` on `logger`, on each deleted test name, and on the replacement test name. **1b is
  right**, and `48f9f65d` appears 0 times in 1a.
- **Classification conflict neither cohort can see.** 1a treats `7014125a` as the recovered plan's
  *baseline* (the plan post-dates it, so its changes are not divergences); this artifact catalogues
  the same commit as four ship **corrections** and raises two of them as contract flips 1 and 7 with
  retired claims the rationale must carry. Both readings are individually sound and they hand Worker
  1 opposite defaults for where the change record starts. Neither cohort establishes the plan's
  *upper* bound, which decides the question: `PLAN-024.md` lists 10 tests and the file held 11 by
  `744fd28d`, so the recovered plan is a snapshot in the window `7014125a` <= plan < `744fd28d`, and
  the log-once sentinel this artifact's flip 2 treats as "what tag 0.0.7 actually shipped" was
  therefore very likely never in the planned contract at all.
- **Complementary, not conflicting.** 1a's `_strawberry_patches.py` citation-rot item and this
  artifact's `docs/TREE.md` item each exist in exactly one catalog. Worker 1 needs the union.

### DRY findings

Not applicable in the usual sense — no code, no abstraction, no existence challenge. One
documentation-level duplication: the `### Post-ship divergence catalog` entries and the
`### Contract flips` section restate the same eight changes in two vocabularies, and M1's wrong count
lives in the catalog while entry 19's correct "7 tests at HEAD" lives three entries later. That is the
shape that let the two disagree. When the catalog and the flips restate one fact, make one the source
and cross-reference the other.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> empty. `__all__` and the re-export list
are unchanged; consistent with this artifact's flip 3 finding that the helper is submodule-path-only.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Its only write is this
artifact.

### Failability proofs

None owed and none recorded: the slice introduces no boundary, guard, gate, or rejection path. My
independent re-run set is therefore **empty**, legal under `worker-3.md` only in exactly this case.
No source file was mutated; the transient-mutation carve-out was not exercised.

### Hot-path budget

Not applicable; the build plan declares no hot path.

### Static helper

`scripts/review_inspect.py` **not run** — recorded skip, same reasons the artifact gives for its own
skip: the pass needs line-level history and executed behavior, not a static overview, and pre-flight
already ran it on `_django_patches.py`.

### Temp test verification

- `docs/builder/temp-tests/024-review/probe_discriminator.py` (gitignored) — my own probe, written
  before reading this artifact's probe output in detail, executed under `/tmp/dsf-floor-024/bin/python`
  and `.venv/bin/python`.
- Disposition: **not promoted.** `tests/test_django_patches.py::test_disallowed_methods_read_prefers_the_class_attribute_shape`
  and `…::test_disallowed_methods_read_falls_back_to_the_connection_feature_flag` already pin both
  branches synthetically; the probe adds only real-interpreter execution at each end of the range,
  which is the floor run's job.
- Additionally executed, because it is a planned verification command no pass in this cycle had run:
  `FAKESHOP_SHARDED=1 uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py --no-cov -q`
  -> **36 passed**. `TEMP-024.md` `## Verification Commands` names it, and the patch's subject is
  multi-database teardown, so the only mode configuring more than one alias had never been executed
  against it. Green; recorded as evidence, not as a finding.

### What looks solid

- **The floor run is the best work in this cycle.** It is a real execution at a real floor, its venv
  survives for re-derivation, its resolved versions match the canonical statement rather than a
  remembered number, and it converts "the audited set spans 5.2.16-6.1" from an assertion into one
  executed point at each end. Every cell of the discriminator table reproduced under an independently
  written probe.
- **Recording that `-e . --group dev` alone resolves *above* the floor** (django 5.2.17,
  strawberry 0.324.0 displaced by the explicit pin) is the detail that proves the explicit pin did
  work, and it is exactly the kind of thing a floor run usually leaves unrecorded.
- **The `is`-vs-`==` note.** A recorded wrong first probe, with the reason it was wrong and the
  instruction for anyone re-deriving. I hit the same trap would-be and the note is correct.
- **Correcting the dispatch rather than inheriting it.** Both corrections reproduce: 5 of the
  dispatch's 13 commits are in-release, and the chronology of `e145ba36` / `7cc163db` / `4a25bf42` is
  the reverse of what the dispatch listed. The observation that reading them in the wrong order makes
  `e145ba36` look like it *reintroduces* em-dashes is a real trap caught.
- **Flip 6's framing.** Naming the `hasattr` discriminator as the flip most likely to be
  re-introduced by a well-meaning reader, and pinning the reason to `_add_databases_failures`
  ignoring a 6.1 subclass's legacy attribute, is the single most useful sentence for Worker 1 in
  either artifact.
- **Every commit hash in this artifact resolves and is a HEAD ancestor** — in a repo whose history
  gets rewritten by concurrent sessions, that is not automatic, as the sibling cohort demonstrates.

### Notes for Worker 1 (spec reconciliation)

- **Escalated — change-record starting point**, with the plan's upper bound as the deciding fact
  (both stated in the cross-cohort section above). Resolution paths: (a) the change record starts at
  `300e2811`, and `7014125a` / `744fd28d` are in-release corrections carrying their own retired
  claims — this artifact's shape; or (b) it starts at the recovered plan's baseline, in which case
  flips 1 and 7 must appear as "the plan already describes the corrected form" rather than as
  divergences. The two artifacts default opposite ways; pick one explicitly.
- Grading this artifact's `### Notes for Worker 1` for usability, as the review is asked to: **9 spec
  facts, all usable** — each names a symbol, a settings key, or a stamped attribute, and each is
  re-derivable from the file. The **rationale bullets are weaker in one place**: "Why reimplement
  rather than delegate, and why that choice is what forces the body pin (the file's own contrast with
  the delegating siblings)" states a conclusion and points at "the file". The evidence is specific —
  the comment block above `_CLASS_ATTRIBUTE_REMOVE_DATABASES_FAILURES_SOURCE` and
  `_django_patches.py::_validate_upstream_shape`'s docstring, which each carry the contrast in one
  sentence. Cite them, or Worker 1 re-derives what this cohort already had.
- The deferred-work catalog for this cycle is the **union** of both artifacts, plus 1a's caveat that
  `_strawberry_patches.py` is under concurrent edit and its citation-rot item must be re-derived
  before homing.
- Do not carry any raw `path:NN` out of either artifact into the spec or rationale (L3).

### Review outcome

`revision-needed`.

Nearly all of this artifact re-derives exactly, including every commit count, the whole test-count
progression, both dispatch corrections, and the entire floor run — which I re-executed rather than
read, and which is accepted in full. The single Medium (M1) is one clause: a `_wrap.py` count stated
as measured that is wrong, sitting beside a correct measured count in the same sentence, and it
mis-attributes which commit brought the two beyond-plan wrap tests. It is a one-line correction for
Worker 2 needing no spec context, which is precisely why it goes back rather than escalating; the
same standard sent the sibling cohort back for its citation defects, and applying it unevenly is what
makes a count defect survive a review. The audit itself does not need redoing.

---

## Build report (Worker 2, pass 2)

Apply-changes pass over the Worker 3 review. **Read-only on all source**: no `.py` file, no spec file, no
build-plan file, no baseline-dirty file was touched, and the floor venv was neither rebuilt nor installed
into. The review's load-bearing verdicts — **no code gap**, and the **floor run accepted in full after
independent re-execution** — were not re-opened. Every fix is to the change record.

### Files touched

- `docs/builder/bld-slice-1b-024-divergence_and_floor.md` — this artifact (body corrected above; this
  report appended).
- `docs/builder/worker-memory/worker-2-024.md` — one appended entry (gitignored, append-only).

### Tests added or updated

None (read-only pass).

### Findings addressed

- **M1 — `_wrap.py` "4 tests unchanged in count" at `7014125a`.** Corrected to **4 -> 6**, with the name
  set of the two added tests and the full decomposition of HEAD's 7 as 4 (`61973f8d`) + 2 (`7014125a`)
  + 1 (`f7fbead4`). Re-measured, not taken from the review:

  ```shell
  git show "61973f8d:tests/test/test_wrap.py"    | grep -c '^def test_'   # 4
  git show "7014125a:tests/test/test_wrap.py"    | grep -c '^def test_'   # 6
  git show "f7fbead4:tests/testing/test_wrap.py" | grep -c '^def test_'   # 7
  grep -c '^def test_' tests/testing/test_wrap.py                         # 7  (HEAD)
  ```

  A name-set diff of the same blobs gives which two: `…_installs_when_database_failure_symbol_missing`
  (the plan's fifth Phase-4 clause, so a *planned* test that had not landed when the plan called the file
  "5 regression tests") and `…_raises_on_non_callable_wrapper` (beyond plan). The entry now says so,
  because "5 planned + 2 beyond" is true of HEAD but not of the order they arrived in.
- **Every other count this re-attribution touches, re-derived — and one more was wrong.** Entry 13's
  "12 -> 13 tests" for `48f9f65d` does not reproduce: the file held **13 before and 13 after**
  (`c7cb5f5c` took 12 -> 13 by adding `test_apply_no_ops_when_toggle_disabled`; `48f9f65d` deletes two
  and adds two). Corrected in place with the reason it matters — a net-zero commit is invisible to a
  count-only record, and this is the commit that retired graceful degradation. The reviewer's own L1 in
  the sibling artifact carries the same slip in its stated progression; that disagreement is recorded in
  1a's `### Notes for Worker 1` item 24 rather than acted on silently, since the review section is not
  mine to edit.
- **Counts that DID reproduce**, re-run rather than inherited, so the reader knows which were checked:
  `tests/test_django_patches.py` 6 (`300e2811`) -> 10 (`7014125a`) -> 11 (`744fd28d`) -> 12 (`e82df83d`)
  -> 13 (`c7cb5f5c`) -> 13 (`48f9f65d`) -> 17 (`0d655bde`) -> 17 (`136c5476`) -> 20 (`eb2a1764`) -> 21
  (`18550f5d`); `tests/test_apps.py` 6 -> 7 (`136c5476`) -> 8 (`18550f5d`); the six `--follow` counts
  13 / 8 / 8 / 13 / 7 / 9, their union of 23 and the surface of 21; the byte sizes 3,855 (`300e2811`),
  6,489 (`893465a5`) and 5,706 (`_wrap.py` at `61973f8d`); the 20 changed lines at `7cc163db`; 36 = 21 +
  7 + 8.
- **L1 — two correct populations read as a contradiction.** The correction's headline now names both:
  five of the dispatch's thirteen (the `_django_patches.py` file history) and six of the twenty-one
  surface commits. The extra in-tag member is `e82df83d`, which touches only
  `tests/test_django_patches.py` and so is absent from the file history the dispatch used.
- **L2 — the catalog is a union.** Stated as its own paragraph beside the escalations, naming what this
  cohort's angle structurally cannot surface (a defect that lives in a document and in no commit) and
  carrying 1a's two items explicitly, including the caveat that the `_strawberry_patches.py` repair
  appears to have already landed uncommitted under the concurrent Slice 3 cohort.
- **L3 — non-transferable citation form.** The `docs/TREE.md` escalation now flags its own `path:NN`
  numbers as legal here and forbidden in the spec or rationale, and states the sentence the spec should
  carry instead.
- **Cross-cohort classification conflict.** Recorded as a **Worker 1 decision** with both readings, the
  cost of each, and the deciding fact measured (below). Not resolved: `docs/builder/BUILD.md`
  `## Spec reconciliation` makes the spec the custodian's.

### The commit-reachability sweep

Run over **both** artifacts' hashes in one pass, since the sibling's dead citations proved this repo's
history is rewritten under concurrent sessions: 34 distinct 8-hex tokens (measured after this pass's
edits), 32 of them commits, of which **30 are HEAD-reachable and exactly 2 are orphans** (`8e86e777`, `e69ff4f9` — both cited only by the
sibling artifact and both now replaced there). The full command set and the patch-id equivalence proofs
are in 1a's pass-2 report and are not repeated here. **Every commit cited by this artifact resolves and is
a HEAD ancestor**, confirming the review's finding on that point; the two orphan tokens present in this
file appear only inside the Worker 3 review section's cross-cohort discussion of the sibling.

### The plan's upper bound, measured

The fact both cohorts flagged as missing and neither had. `TEMP-024.md` as recovered is byte-identical to
its `7014125a` blob; `PLAN-024.md` differs from its `7014125a` blob by exactly two lines, both mechanical
reference rewrites carrying no contract. Both documents therefore describe the tree as of `7014125a` and
nothing after it — so the window the cohorts guessed (`7014125a` <= plan < `744fd28d`) is confirmed and
pinned to a point, and the log-once **sentinel** was never part of the planned contract. Commands and the
consequence for this artifact's flip 2 are in the escalation above.

### Failability proofs

None; this pass introduced no boundary. It is read-only on all source and edits Markdown only.

### Hot-path budget

Not applicable; plan declares no hot path, and this pass changes no code.

### Floor verification

**Not re-run, deliberately.** The plan assigns the floor run to this slice and the first pass performed
and recorded it; the Worker 3 review then re-executed the whole of it — venv resolution, the focused
scope, and the discriminator table under an independently written probe — and accepted it in full, with
every one of the twelve version cells reproducing. The dispatch for this pass declares floor scope
**none**. Re-running it would neither test anything the review left open nor produce a more independent
result than the review's, and rebuilding the venv would destroy the artifact a later reader can
re-derive from. `/tmp/dsf-floor-024` is left exactly as it was; **no `uv pip install` was issued in this
pass**, into it or into the shared `.venv`.

### Validation run

- `uv run ruff format <files this pass touched>` — **not run**: this pass touched no `.py` file.
- `uv run ruff check --fix <the same files>` — **not run**, same reason.
- `git status --short` after the pass — the only entries attributable to it are this artifact and
  `docs/builder/bld-slice-1a-024-planned_vs_head.md`. Everything else is the build plan's baseline-dirty
  set, the concurrent Slice 3 cohort's `M django_strawberry_framework/_strawberry_patches.py`, or the
  build plan itself. Nothing reverted, nothing tidied.
- No `pytest` run: no assertion changed, and no correction in this pass is a behavioural claim.

### Implementation notes

- Every number restated in the corrected text was re-measured in this pass, including numbers pass 1 got
  right — which of them had been measured is not recoverable by reading them, and two of the ones checked
  turned out wrong (`_wrap.py` at `7014125a`, and `tests/test_django_patches.py` at `48f9f65d`).
- Counts are **occurrences**, from the shortest distinctive token: `grep -c '^def test_'` on extracted
  blobs, `grep -oE '\b[0-9a-f]{8}\b'` for hashes, name-set `diff` where a count could not distinguish a
  net-zero change from no change. The `48f9f65d` slip is precisely what a count alone cannot see.
- Historical reads are `git show <rev>:<path>` into `/tmp/dsf-024-fix/` (outside the repo) followed by
  `diff`. No `git stash`, `git checkout`, `git restore`, or `git worktree` at any point.

### Notes for Worker 3

- The diff for this pass is two Markdown files; nothing in source. The Worker 3 review sections in both
  artifacts were left untouched.
- Worth re-deriving: the `4 -> 6` wrap count and its name-set diff, the `13 -> 13` correction at
  `48f9f65d` (and with it the `c7cb5f5c` step the review's L1 progression omits), and the plan's
  two-line upper-bound diff.

### Notes for Worker 1 (spec reconciliation)

This pass adds no new spec fact. The nine `**Facts for the spec**` above are unchanged and still stand;
what changed is the escalation block, which now carries the change-record starting point as an explicit
decision with the deciding measurement attached, and the statement that the deferred-work catalog is the
union of both cohorts' lists rather than either one.

---

## Review (Worker 3, pass 2)

Re-review of the apply-changes pass, not a fresh review. The **floor pass** — including the
discriminator table under an independently written probe — was reproduced by the prior pass and is not
re-opened; `/tmp/dsf-floor-024` was not re-run and no `uv pip install` was issued in this pass, into it
or into the shared `.venv`. The subject is narrow: did the fixes land, are the *new* numbers true, and
did the repair introduce anything.

The tree-state note, the full 34-token reachability sweep, the M2 split verification, the plan
upper-bound verification, and the adjudication of 1a note 24 were performed once across **both**
artifacts and are recorded in 1a's `## Review (Worker 3, pass 2)` rather than duplicated here. Their
results as they bear on this artifact: **every commit cited by this artifact resolves and is a HEAD
ancestor** (the only two orphan tokens present are inside this file's own review section at line 1128
and its pass-2 report at line 1330, both discussing the sibling); and `HEAD` has moved to `f466863a`,
whose single intervening commit touches **none** of the six surface files, so no number here needs
re-deriving.

### Sample declaration: what I re-derived, and what I accepted unchecked

**Re-derived in this pass (all reproduce exactly):**

| Claim | Command | Result |
|---|---|---|
| M1's fix — `_wrap.py` 4 -> 6 at `7014125a` | `git show ${h}:tests/test/test_wrap.py \| grep -c '^def test_'` on `61973f8d` then `7014125a` | **4**, then **6** |
| the two names `7014125a` adds | name-set `diff` of the same two blobs | `+test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing`, `+test_safe_wrap_connection_method_raises_on_non_callable_wrapper` — exactly as the entry now states, and the first is the plan's fifth Phase-4 clause |
| HEAD's 7 = 4 + 2 + 1 | `git show 4a25bf42:tests/testing/test_wrap.py \| grep -c`; `git show f7fbead4:… \| grep -c`; name-set `diff`; `grep -c` on the working file | **6** before `f7fbead4`, **7** after, the delta being `+test_safe_wrap_connection_method_keeps_type_error_boundary_for_hostile_repr`; HEAD **7**. The decomposition holds and the `TypeError` boundary's coverage is `7014125a`'s, not `f7fbead4`'s |
| entry 13's new count — `48f9f65d` is 13 -> 13 | `git show ${h}:tests/test_django_patches.py \| grep -c '^def test_'` on `e82df83d` / `c7cb5f5c` / `48f9f65d`; name-set `diff` of each pair | **12 / 13 / 13**; `c7cb5f5c` adds `test_apply_no_ops_when_toggle_disabled`; `48f9f65d` is **-2 / +2**, the four names being the two deletions and the two `…fails_loudly…` replacements. **The builder's own new finding is correct.** |
| the counts the pass says "DID reproduce" | each re-run rather than accepted | progression **6, 10, 11, 12, 13, 13, 17, 17, 20, 21**; `tests/test_apps.py` **6 -> 7** (`136c5476`) **-> 8** (`18550f5d`); the six `--follow` counts **13 / 8 / 8 / 13 / 7 / 9**; union **23**, surface **21**; byte sizes **3855** (`300e2811`), **6489** (`893465a5`), **5706** (`_wrap.py` at `61973f8d`); **20** changed lines at `7cc163db`; 36 = 21 + 7 + 8 |
| L1's fix — both populations named | read the corrected headline against its table | "five of the dispatch's thirteen" / "six of the twenty-one surface commits", and the extra in-tag member is named as `e82df83d`. Re-measured: **5** of the 13-commit `_django_patches.py` history and **6** of the 21-commit surface are ancestors of `0.0.7` |
| the 6 / 15 split membership | `merge-base --is-ancestor <h> 0.0.7` over all 21 | membership identical to the table, cell for cell |
| entry 4's stated cause | `git show 7014125a:…/_django_patches.py` read around `apply()` | the docstring says "logs a single ``INFO``-level notice" while the body calls `logger.info` unconditionally — the claim-before-mechanism reading is correct and reproduces from the blob |
| flip-2 / flip-5 / flip-6 after-states at HEAD | read `django_strawberry_framework/_django_patches.py` | unchanged from the prior review's reading; `grep -c logger` -> **0** |
| symbol citations resolve | every backticked identifier in the body checked against the set of every identifier in every non-`docs` `.py` in the tree | **5 non-resolving tokens, all of them deliberately-cited retired symbols** (`_PATCH_APPLIED`, `_missing_symbol_logged`, the two deleted test names, `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`). **No dangling citation in this artifact** — including the four reload-safety names at lines 397-399, which are right where the sibling's are wrong (1a M1) |
| public-surface check | `git diff HEAD -- django_strawberry_framework/__init__.py` | **empty** |
| no source touched | `git status --short \| grep '\.py$'` | one entry, `_strawberry_patches.py`, the concurrent Slice 3 cohort's |

**Accepted unchecked (named, so the sample is honest):** the `docs/TREE.md` line numbers in the third
escalation; the per-commit `diff -u … | grep -c '^[+-][^+-]'` changed-line counts other than `7cc163db`'s;
the prose classification (`correction` / `serves-later-work` / cosmetic) of entries 6, 8, 10, 11, 16, 20;
the commit-message quotations in entries 12 and 18; the `docs/GLOSSARY.md` wording in the second
escalation (baseline-dirty, out of this cycle's scope).

### High:

None.

### Medium:

None.

### Low:

#### L1 — "Neither touches a decision" is false of the line, true of its content

The escalation's upper-bound block says the two-line `PLAN-024.md` delta is "both mechanical reference
rewrites carrying no contract", which is exactly right and reproduces; 1a's mirror of the same block adds
"Neither touches a decision, a DoD item, or a test name", which is not — line 92 sits inside decision
D-4's bullet and line 115 inside DoD item 9c. What neither changes is the decision's *content*.

This artifact's own wording is the better of the two and is the one to carry forward.
**Disposition: recorded, not held** — the claim Worker 1 acts on is unaffected, and the correction is
stated in full in 1a's re-review so the sentence is not inherited verbatim into the rationale.

### Adjudication of the recorded disagreement

Recorded in full in 1a's `## Review (Worker 3, pass 2)`. In one line: **the builder is upheld.** The
prior review's L1 *finding* is correct and applied; its stated *progression* omits `c7cb5f5c` and so
attributes the 12 -> 13 step to `48f9f65d`, which measures 13 -> 13. This artifact's entry 13 now states
the corrected form with the reason it matters, and the reasoning is sound: a `-2/+2` commit is invisible
to a count-only record, and it is the commit that retired graceful degradation.

Worth naming for the record, because it also indicts an instrument this artifact and its reviewer both
used: **the same nine `(commit, count)` pairs are individually true and collectively misleading.** Every
pair in the review's progression reproduces, `48f9f65d` included. The defect is the omitted commit
between two of them, and no per-pair check could have found it — only the name-set `diff` the builder ran
distinguishes "no change" from "two out, two in".

### The cross-cohort conflict's deciding fact — verified

Verified from the blobs and recorded in full in 1a's re-review. Results as they bear on this artifact:
the recovered `TEMP-024.md` is byte-identical to its `7014125a` blob; the recovered `PLAN-024.md` differs
from its `7014125a` blob by exactly two lines, both mechanical; both recovered files are byte-identical
to their `d1d19ca2^` blobs, so the recovery is faithful. **The window collapses to the point `7014125a`,
as claimed.**

The consequence this artifact draws for its own flip 2 also holds independently: `744fd28d`
(2026-05-26T15:09) and `e82df83d` (15:27) both post-date the plan's last content-bearing write at 10:21,
and the `7014125a` blob's docstring promises "a single ``INFO``-level notice" over an `apply()` that logs
on every call. So flip 2's state B is correctly described as "what tag `0.0.7` actually shipped" **and**
correctly qualified as carrying a sentinel that was never in the *planned* contract. Both statements can
be true at once and the escalation says so.

**The conflict is still Worker 1's and is not silently resolved.** The escalation is headed
`[DECISION — Worker 1's, as spec custodian]`, states both readings and the cost of each, and picks
neither. Confirmed by reading the block end to end.

### Regression check on the repair

- **Cross-references with 1a agree** on every shared fact re-derived: the 21 / 6 / 15 split, the corrected
  test-count progression including `c7cb5f5c`, the wrap decomposition 4 + 2 + 1, the `48f9f65d` /
  `0d655bde` split, the plan's upper bound, the catalog-is-a-union statement, and the escalation framing.
  The one live cross-cohort contradiction is 1a's, not this artifact's (1a M1: `_PATCH_ORIGINAL`), and
  this file's lines 397-399 carry the correct names.
- **No entry contradicts another within 1b.** The former disagreement between the catalog and the flips —
  M1's wrong wrap count in entry 3 against entry 19's correct "7 tests at HEAD" — is closed, and the
  correction states the decomposition in the entry that was wrong rather than only in the one that was
  right. Entry 13's counts now agree with the progression restated in the pass-2 report.
- **`### Notes for Worker 1` is usable as the sole input to the spec rewrite.** Walked all nine
  `**Facts for the spec**`: each names a symbol, a settings key, a stamped attribute, or a dispatch order,
  and each re-derives from `django_strawberry_framework/_django_patches.py` as written — item 6's four
  reload-safety names verify exactly. The five `**Explanations for the rationale companion**` each name
  the commits or the docstring the explanation comes from; the prior review's complaint that the
  reimplement-vs-delegate bullet "points at the file" is unfixed in wording but harmless, since the
  reviewer already named the two sites. The three escalations each name a file, a defect, and the reason
  it is out of scope.
- **Nothing was introduced.** No `.py`, spec, build-plan, or baseline-dirty file was modified; the floor
  venv was not rebuilt; `git diff HEAD -- django_strawberry_framework/__init__.py` is empty.

### DRY findings

The prior review's documentation-level duplication stands and is not aggravated: the catalog entries and
`### Contract flips` still restate the same eight changes in two vocabularies. The repair improved it in
the way that matters — the two vocabularies no longer *disagree* — but did not single-source them. For
Worker 1 rather than a hold: when Slice 2 lifts these into the rationale, make one the source and
cross-reference the other, because the duplication is what let entry 3 and entry 19 diverge in the first
place. No code, no abstraction, no existence challenge.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged, consistent with this artifact's flip 3 finding that `safe_wrap_connection_method` is
reachable only at the `django_strawberry_framework.testing` submodule path.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Its only write is this artifact.

### Failability proofs

None owed and none recorded: the pass introduces no boundary, guard, gate, or rejection path and edits
Markdown only. My independent re-run set is therefore **empty**, legal under `worker-3.md` in exactly this
case. No source file was mutated; the transient-mutation carve-out was not exercised.

### Hot-path budget

Not applicable; the build plan declares no hot path and this pass changes no code.

### Floor verification

**Accepted on the prior review's record and deliberately not re-run**, per this pass's dispatched scope of
**none**. The builder's decision not to re-run it is correct and is reasoned correctly in its report: the
prior reviewer re-executed the venv resolution, the focused scope, and the discriminator table under an
independently written probe, and rebuilding the venv would destroy the artifact a later reader
re-derives from. `/tmp/dsf-floor-024` was not touched in this pass and no `uv pip install` was issued.

### Static helper

`scripts/review_inspect.py` **not run** — recorded skip, same grounds as the prior pass: this review
re-derives git history and Markdown claims rather than new logic, pre-flight already ran it on
`_django_patches.py`, and no repeated-literal or import-boundary evidence was needed for any finding.

### Temp test verification

- `docs/builder/temp-tests/024-rereview/` — no temp test was needed; every claim in scope was settled by
  read-only git and `grep` measurement. The one throwaway instrument written (a backticked-symbol resolver
  run over both artifacts) produced no finding against this file.
- Disposition: **nothing to promote.**

### What looks solid

- **The M1 fix corrects the attribution, not just the arithmetic.** Stating 4 -> 6 would have been
  compliance; naming the two tests, marking one of them as the plan's own fifth Phase-4 clause, and
  saying that the `TypeError` boundary's coverage belongs to the commit that *created* the boundary
  rather than the one that narrowed its message is what the rationale actually needs. Both name-set diffs
  reproduce.
- **The pass found a second wrong count with no finding against it.** Entry 13's 12 -> 13 was inherited,
  not challenged, and re-measuring it turned up 13 -> 13. That is `## Claims are proven mechanically`
  applied to the pass's own inherited numbers, which is the case where it is easiest to skip.
- **L1's fix names the population in both halves** rather than reconciling two correct numbers into one
  wrong one. Both re-measure.
- **The floor run remains the strongest evidence in this cycle** and the pass was right to leave it alone.
- **Every commit cited by this artifact resolves and is a HEAD ancestor**, re-confirmed under the full
  34-token sweep and against a HEAD that has since moved.

### Notes for Worker 1 (spec reconciliation)

- **The change-record starting point remains yours**, now with the deciding measurement verified: both
  planning documents describe the tree at exactly `7014125a`. Under either option the log-once
  **sentinel** must not be described as a planned deliverable — the plan promised the INFO-notice no-op,
  and `744fd28d` built the mechanism that made the already-shipped claim true.
- **Prefer this artifact's wording for the reload-safety contract** (`**Facts for the spec**` item 6). The
  sibling's item 7 names `_PATCH_ORIGINAL`, which has never existed at any revision — held there as 1a's
  Medium M1.
- **The deferred-work catalog is the union of both cohorts' lists.** This artifact states so explicitly
  and carries 1a's two items; 1a carries this artifact's `docs/TREE.md` item. Item 19's
  `_strawberry_patches.py` measurement must be re-derived before homing — at this pass the repair is
  present and uncommitted (HEAD blob 1 occurrence, working tree 0), owned by the concurrent Slice 3
  cohort.
- **Do not carry any raw `path:NN` out of this artifact** into the spec or rationale; the escalation
  already flags its own `docs/TREE.md` numbers as non-transferable and states the replacement sentence.
- **HEAD has moved to `f466863a`** since this artifact was written. No surface file changed; nothing needs
  re-deriving.

### Review outcome

`review-accepted`.

The single Medium this artifact was sent back for is closed and closed properly — `_wrap.py` 4 -> 6 at
`7014125a`, with the two test names, the corrected 4 + 2 + 1 decomposition, and the attribution
consequence stated in the entry that was wrong. Both Lows are closed. Re-measuring the counts the fix
touched turned up a second defect the review missed (entry 13's 12 -> 13 is really 13 -> 13), which is
the pass finding its own error rather than defending an inherited number. Every count I re-derived
reproduces, every commit cited resolves and is a HEAD ancestor, the floor run stands accepted, the
cross-cohort conflict is still presented as Worker 1's with its deciding fact now verified, and the
`### Notes for Worker 1` section is usable as the sole input to the spec rewrite.

One Low is recorded above with its resolution and is not held: a wording clause in the shared upper-bound
block that this artifact states correctly and the sibling overstates. Nothing else in this artifact needs
another pass.

---

## Final verification (Worker 1)

Slice contract, from the build plan's `## Declarations`: "what changed after the ship, why, and which
changes flipped a contract?", plus ownership of the cycle's single floor run, read-only on all source and
writing this artifact only. Delivered on all three.

- **Spec slice checklist:** none exists — the archived spec carried no `## Slice checklist`, which the
  artifact records correctly. Nothing to audit or defer.
- **Both dispatch corrections re-derived and upheld.** The surface is **21** commits (`--follow` union 23
  minus `b972cd84` / `dfa035b4`), split **6 in-tag / 15 post-tag** measured per commit against tag `0.0.7`;
  the dispatch's premise that all 13 listed commits were post-ship is false, and the correction's
  population-naming fix reads correctly at close. The chronology correction (`e145ba36` -> `7cc163db` ->
  `4a25bf42`) reproduces.
- **The contract flips are the load-bearing output and all eight survived into the spec or the rationale.**
  Flips 1, 2, 3, 4, 5, 6, 7, and 8 each land as a stated contract in the rewritten spec and as a "claims
  this Decision may no longer make" entry in the rationale companion. Flip 6 is carried with the emphasis
  this artifact asked for: the spec states the `_add_databases_failures`-wraps-the-feature-list mechanism as
  contract, and the rationale says in terms that a future "simplification" back to `hasattr` reintroduces a
  known defect that shipped and survived ten days.
- **The nine `**Facts for the spec**` are all in the spec**, and item 6's four reload-safety names verify
  exactly against `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor`. This
  artifact's wording was preferred over the sibling's, as its reviewer recommended.
- **Floor run accepted without re-running it.** It was performed by this pass, independently re-executed in
  full by the review (venv resolution, focused scope, and the discriminator table under a separately written
  probe), and every version cell reproduced there. `worker-1.md` `## Final test-run gate` requires the gate
  to confirm a floor run happened rather than to own a second one; rebuilding `/tmp/dsf-floor-024` would
  destroy the artifact a later reader re-derives from. The declared floor matches
  `docs/builder/BUILD.md` `## Floor verification`'s single canonical statement — Django `5.2.16`, Python
  `3.10`, strawberry-graphql `0.316.0` — and is not restated from any other document. No `uv pip install`
  was issued by this pass, into that venv or the shared one.
- **Citation form honoured.** The `docs/TREE.md` escalation's raw `path:NN` numbers are legal here and were
  **not** carried out: the spec states "the module summary lines … are rendered into `docs/TREE.md`" with the
  three modules named by full path and no line numbers anywhere.
- **Every commit cited by this artifact resolves and is a HEAD ancestor**, re-confirmed at close against the
  moved HEAD `f466863a`, whose single intervening commit touches none of the six surface files.
- **Deferred work:** this artifact's `docs/GLOSSARY.md` and `docs/TREE.md` items are carried into the Slice 2
  artifact's catalog as part of the union with 1a and 3, each re-derived rather than copied.
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
