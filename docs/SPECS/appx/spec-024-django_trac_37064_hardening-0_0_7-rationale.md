# Rationale: spec-024 — Django Trac #37064 hardening + `safe_wrap_connection_method` (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-024-django_trac_37064_hardening-0_0_7.md`][spec-024]. The spec is the contract and states only what the code must do; everything that explains **how it got there** lives here: the derivation behind each of the eleven Decisions, the alternatives each rejected, every change a Decision has undergone with the commit that made it, and every claim a Decision may no longer make.

## Provenance of this record

**This pass performed a RECONSTRUCTION, not a move.** That distinction is load-bearing and a reader must be able to tell which they are holding.

The [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass normally **cuts** a deliberative layer out of an over-long spec. There was nothing to cut here. Until this cycle, `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` was a **1,618-byte card-snapshot stub** (`git show HEAD:<path> | wc -c` -> `1618`) carrying a card snapshot, a one-word planning note (`shipped`), and two `## Other` bullets. It had no slice checklist, no Decisions, no test plan, and no definition of done; its own preamble said so and instructed a later author to expand it. So no sentence below was moved out of the spec — every one was **rebuilt** from three sources:

1. **Two deleted planning documents**, recovered read-only and never restored to the tree:
   - `docs/PLAN-trac-37064-database-teardown.md` — the Context, the fix description, five named implementation decisions, four risks and open questions, a nine-item definition of done, an out-of-scope list, and a Phase-4 update adding the consumer-facing helper.
   - `docs/TEMP-trac-37064-test-plan.md` — the sources checked, the test-placement decision, the required-test list, the mixed-strategy argument, and the verification commands.

   Both were deleted at `d1d19ca2` (2026-05-27) and recovered from `d1d19ca2^`. Neither carried a glossary-term list; the spec's terms companion is [`spec-024-django_trac_37064_hardening-0_0_7-terms.csv`][spec-024-terms], and this cycle added no term to it. Both recovered copies are **byte-identical to their `d1d19ca2^` blobs**, so the recovery is faithful and "as recovered" is doing no hidden work.
2. **The commit history of the six surface files** — `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/testing/_wrap.py`, `django_strawberry_framework/apps.py`, `tests/test_django_patches.py`, `tests/testing/test_wrap.py`, `tests/test_apps.py` — 21 commits touching the Trac #37064 surface, 6 of them inside tag `0.0.7` and 15 after it.
3. **The shipped source itself**, read against every recovered sentence.

A reconstruction has a weakness a move does not: where a change's commit message does not state its cause, the cause is an **inference** from the diff and from the successor commit. Every such entry below says so in place rather than smoothing it over.

### Where the change record starts, and the reading rejected

Two audit cohorts handed this pass opposite defaults, and the choice belongs to the spec custodian ([`docs/builder/BUILD.md`][build] `## Spec reconciliation`).

**Chosen — the change record starts at the ship commit `300e2811` (2026-05-23).** Everything the card shipped and later changed is in the record, with each entry marked in-release or post-tag. Two consequences follow, and both are wanted: the `TransactionTestCase` install target and the `_PATCH_APPLIED` flag appear as retired claims rather than vanishing, and a reader of the shipped `0.0.7` artifact can find every claim they would hit.

**Rejected — the change record starts at the recovered plan's baseline.** The plan post-dates the ship, so under that reading `7014125a`'s four corrections are not divergences at all and simply disappear from the record. It loses on two counts. First, the record's subject is the card, not the recovered document: card `DONE-024-0.0.7` shipped `300e2811`, and a change record whose origin depends on which deleted file happened to survive in git is not a record of the card. Second, it silently drops two contract flips — the install target and the idempotence mechanism — that a reader of the shipped tag would still hit, and the only way to keep them is a hedge ("the plan already describes the corrected form") that is exactly the chronology the spec is forbidden to carry and that this file exists to hold instead.

**The deciding fact, re-derived by this pass rather than inherited.** The recovered plan's upper bound is not a window; it is a point:

```shell
git show 7014125a:docs/TEMP-trac-37064-test-plan.md         > <scratch>/temp-7014125a.md
git show 7014125a:docs/PLAN-trac-37064-database-teardown.md > <scratch>/plan-7014125a.md
diff <scratch>/temp-7014125a.md <recovered TEMP>   # rc=0, identical
diff <scratch>/plan-7014125a.md <recovered PLAN>   # rc=1, exactly two changed lines
```

`TEMP` as recovered is byte-identical to its `7014125a` blob. `PLAN` as recovered differs from its `7014125a` blob by exactly two lines, both mechanical reference rewrites carrying no contract: an `AGENTS.md` line-number citation rewritten to the symbol-qualified form (`df547235`, the repo-wide line-NN sweep), and a `spec-019-…` path gaining its `SPECS/` prefix (`974189ad`). The first sits inside the escape-hatch decision's own bullet and the second inside the definition of done's version-target sub-bullet; what neither **changes** is a decision's content, a definition-of-done item's content, or a test name.

**Both planning documents therefore describe the tree at exactly `7014125a`, and nothing after it.** One consequence is carried in [Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers) below and must not be lost: `744fd28d`'s log-once **sentinel** was never part of the planned contract. What the plan promised was the missing-symbol **no-op with one INFO notice** — which is `7014125a`'s state, where the docstring claimed "a single INFO-level notice" over an `apply()` that logged on every call. The sentinel was built afterwards to make an already-shipped claim true. The rationale must not describe it as a planned deliverable, and does not.

## Change record — the 21 commits that moved this surface

Six are inside tag `0.0.7` (`72f6cd9b`), fifteen are after it; membership measured per commit with `git merge-base --is-ancestor <sha> 0.0.7`. Every date is the **author** date (`git log --format=%ad --date=short`) — the date the change was made, which is what each row's claim rests on; `52d97ec0` is the only one of the 21 whose committer date differs (2026-05-30). Every hash below was proved HEAD-reachable with `git merge-base --is-ancestor <sha> HEAD` at the time of writing — a precaution, not a formality, since this repository's history is rewritten under concurrent sessions and an earlier pass of this cycle cited two hashes that resolve in no fresh clone.

| Commit | Date | Release | What it did |
|---|---|---|---|
| `300e2811` | 2026-05-23 | in `0.0.7` | The ship. Patch module created; installed on `TransactionTestCase`; `_PATCH_APPLIED` first-call-wins flag; 6 tests. |
| `893465a5` | 2026-05-23 | in `0.0.7` | Module docstring only: the `django-debug-toolbar` ecosystem precedent and the wrap-time / unwrap-time framing. No executable line. |
| `61973f8d` | 2026-05-23 | in `0.0.7` | Phase 4: the `_wrap.py` helper and its 4 tests; glossary entries. |
| `7014125a` | 2026-05-26 | in `0.0.7` | Four in-release corrections — retarget to `SimpleTestCase`; guarded `_DatabaseFailure` import plus `_is_database_failure`; `_PATCH_APPLIED` -> `_patch_is_installed()`; the helper's non-callable `TypeError`. Patch tests 6 -> 10, wrap tests 4 -> 6. **The state both recovered planning documents describe.** |
| `744fd28d` | 2026-05-26 | in `0.0.7` | `_missing_symbol_logged` sentinel, so the missing-symbol INFO fires once as the docstring already claimed; the helper's `Raises:` example corrected from a bound method to the cursor object. Patch tests 10 -> 11. |
| `e82df83d` | 2026-05-26 | in `0.0.7` | Adds the `_patch_is_installed()` `installed is None` branch test. 11 -> 12. |
| `52d97ec0` | 2026-05-29 | post-tag | Test layout only: one assertion re-wrapped for the line-length / trailing-comma rule. |
| `e145ba36` | 2026-06-01 | post-tag | `test/` -> `testing/` rename, package and tests, plus every documented import path. |
| `b8a8a6e0` | 2026-06-01 | post-tag | Helper docstring: an RST subsection folded into a bold run; the example gains its missing import. |
| `7cc163db` | 2026-06-10 | post-tag | ASCII-only sweep across all six files. One executable string: the log message's em dash, itself retired later. |
| `4a25bf42` | 2026-06-12 | post-tag | Module summary first lines for `_django_patches.py`, `apps.py`, `testing/_wrap.py` — inputs to [`docs/TREE.md`][tree]. |
| `7c2a63ed` | 2026-06-12 | post-tag | The same for the three test modules' summary lines. |
| `c7cb5f5c` | 2026-06-18 | post-tag | The global `APPLY_UPSTREAM_PATCHES` gate arrives alongside two sibling patch modules; `ready()` goes from one applier to three. Patch tests 12 -> 13. |
| `48f9f65d` | 2026-07-11 | post-tag | **The fail-loud reversal.** Import-time capture of the original; `_validate_upstream_shape` tiers 1-2; `logger`, `logger.info` and `_missing_symbol_logged` deleted; two tests deleted and two added, so 13 -> 13. |
| `0d655bde` | 2026-07-13 | post-tag | The body pin (tier 3), unreadable source treated as drift; per-dependency gating and escape-hatch wording in every drift message (the `conf.py` half is `a62d6dca`, same day); the negative test switched to the live import-time capture. 13 -> 17. |
| `136c5476` | 2026-07-13 | post-tag | `ready()`'s three-applier dispatch pinned deterministically; `apps.py` docstrings stop repeating each module's bug inventory. |
| `5a74d803` | 2026-07-30 | post-tag | Test comment prose only: review bookkeeping stripped. |
| `eb2a1764` | 2026-08-06 | post-tag | Django `6.1` removed the class attribute, the single pin matched neither shape, and `ready()` raised — the package refused to boot on `6.1`. The pin becomes a two-member audited set; `_disallowed_connection_methods` added. 17 -> 20. |
| `18550f5d` | 2026-08-16 | post-tag | Reload-safe descriptor capture; the discriminator changes from `hasattr(cls, …)` to the validated body source. 20 -> 21. |
| `f7fbead4` | 2026-08-16 | post-tag | The helper's `TypeError` message stops interpolating the wrapper. Wrap tests 6 -> 7. |
| `36cd1925` | 2026-08-18 | post-tag | Test comment prose only. |

Patch-module test-count progression, measured per commit with `git show "<sha>:tests/test_django_patches.py" | grep -c '^def test_'`: **6** (`300e2811`) -> **10** (`7014125a`) -> **11** (`744fd28d`) -> **12** (`e82df83d`) -> **13** (`c7cb5f5c`) -> **13** (`48f9f65d`, two deleted and two added) -> **17** (`0d655bde`) -> 17 (`136c5476`) -> **20** (`eb2a1764`) -> **21** (`18550f5d`, and HEAD). The `48f9f65d` step is the one a count-only record cannot see: it is net zero and it is the commit where graceful degradation was retired. Wrap-module tests decompose as **4** (`61973f8d`) **+ 2** (`7014125a`) **+ 1** (`f7fbead4`) = 7, so the `TypeError` boundary's coverage belongs to the commit that created the boundary, not to the one that later narrowed its message.

## Decision 1 — A private patch module per dependency, applied from ready()

Spec text: [Decision 1][spec-024-d1]. Contract that stays: a private `_django_patches` module, one patch module per third-party dependency, all dispatched from `ready()` behind function-local imports.

### Derivation

- A private module keeps `apps.py` short and gives future Django patches a natural home. The leading underscore is the visibility signal; consumers never import it.
- `ready()` is Django's canonical one-time-setup hook and fires once after all apps load, which is exactly the lifecycle point at which `SimpleTestCase` is importable and the patch has not yet been needed.
- Function-local imports in `ready()` mean importing `apps` outside a configured Django project pulls in no patch module.

### Alternatives considered (and rejected)

- **Inline the patch in `apps.py`.** Rejected: the patch carries far more rationale than code, and inlining it would bury the `AppConfig` shape (which is a different card's contract) under it.
- **A single patch module for every dependency.** Rejected once a second and third dependency needed patching: the settings surface is keyed per dependency, so one module per dependency keeps `UPSTREAM_PATCH_DEPENDENCIES` and the module list in one-to-one correspondence and makes an opt-out mean exactly one module.

### Changes this Decision underwent

- **`c7cb5f5c`** turned `ready()` from one applier into three, adding `_strawberry_patches` and `_cross_web_patches` for a different card's bug. The Trac #37064 applier stayed first and otherwise unchanged; this card's module became one of three passengers on a shared dispatch site.
- **`136c5476`** removed the per-module bug inventory that `apps.py`'s docstrings had been repeating, making each patch module's own docstring the single source of truth.

### Claims this Decision may no longer make

- **That "additional patches land as more functions in the same module".** True only within Django. The organizing rule at HEAD is one module per *dependency*, each with its own `apply()`.
- **That the patch is "~30 lines of code with a 30-line rationale docstring".** The module was 91 lines at `300e2811` and is 406 at HEAD. The scale claim is retired; the isolation argument it supported is not.

## Decision 2 — The patch installs on `SimpleTestCase`

Spec text: [Decision 2][spec-024-d2]. Contract that stays: install on the definition site; the hierarchy inherits.

### Derivation

Django defines `_remove_databases_failures` on `SimpleTestCase`. Patching the definition site covers `TransactionTestCase`, `TestCase`, and every direct `SimpleTestCase` subclass in one assignment, and covers them through the same MRO Django itself relies on.

### Alternatives considered (and rejected)

- **Install on `TransactionTestCase`.** Rejected — and this is not a hypothetical: it is what the card shipped. A direct `SimpleTestCase` subclass with `TransactionTestCase` nowhere in its MRO bypassed the net entirely, which is a correctness hole in the shipped artifact rather than a stylistic preference.

### Changes this Decision underwent

- **`7014125a`** retargeted the install from `TransactionTestCase` to `SimpleTestCase` and followed it through the module docstring, `ready()`'s docstring, and the helper's reference to `_add_databases_failures`. The ship's own test was named for the wrong class and was renamed with it.

### Claims this Decision may no longer make

- That the package ships a "defensive replacement for `django.test.testcases.TransactionTestCase._remove_databases_failures`". That sentence was in the shipped tag's docstring for four days and is false.

## Decision 3 — The replacement reimplements the loop behind one guard

Spec text: [Decision 3][spec-024-d3]. Contract that stays: upstream's loop, reimplemented, with one `isinstance` guard and one read helper.

### Derivation

- The `isinstance(method, _DatabaseFailure)` guard **is** the patch proposed in the upstream ticket. Keeping the replacement otherwise faithful to upstream is what makes "strictly defensive" checkable rather than asserted.
- The guard restores the symmetry Django's own docstring claims: `_add_databases_failures` and `_remove_databases_failures` operate on the methods *they* wrapped, and the patched form simply declines to crash on a method the pair never owned.

### Alternatives considered (and rejected)

- **Wrap and delegate to upstream's method instead of reimplementing it.** Rejected: the crash is *inside* the loop upstream runs, so a wrapper cannot intercept the individual `method.wrapped` access without re-running the loop itself. The rejection has a standing cost, and the spec states it as contract: because the module reimplements rather than delegates, an upstream body change does not flow through the patch, which is the entire reason [Decision 5](#decision-5--two-audited-upstream-bodies-discriminated-by-the-validated-source)'s body pin exists. The sibling patch modules *do* delegate and consequently need only their call shape validated. The contrast is written into the source at `django_strawberry_framework/_django_patches.py #"WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP"`'s surrounding comment and restated in `django_strawberry_framework/_django_patches.py::_validate_upstream_shape`'s docstring.
- **Uninstall Django's wrapper and reinstall it around the risky window** — the `django-debug-toolbar` cache-panel owner-sentinel shape. Rejected because the package does not own `_DatabaseFailure`; the pattern needs the wrapper's owner. It remains the right answer for any future package-owned connection instrumentation, and that conclusion survives in the module docstring's ecosystem-precedent section as the pattern explicitly *not* available here.

### Changes this Decision underwent

- **`eb2a1764`** replaced the inline `cls._disallowed_connection_methods` read with a call to the new `_disallowed_connection_methods` helper, so one replacement body could cover both audited upstream shapes.

### Claims this Decision may no longer make

- **That `_patched_remove_databases_failures` is a "verbatim copy of Django's `_remove_databases_failures` body with an `isinstance` guard added".** The method-list read is delegated to `_disallowed_connection_methods` and is no longer upstream's line. The `isinstance` guard — the part that is the ticket's own proposal — is unchanged.

## Decision 4 — Fail-closed upstream validation in three tiers

Spec text: [Decision 4][spec-024-d4]. Contract that stays: validate, then install, or raise.

### Derivation

Two facts force the tiers. The module reads Django private symbols (`_DatabaseFailure`, a private classmethod), and it supersedes a body rather than delegating to one. Either can drift silently. Silently dropping a defensive patch leaves a consumer believing they have protection they do not have; refusing to install is loud, and is only tolerable because an explicit opt-out exists to recover from it ([Decision 6](#decision-6--apply_upstream_patches-is-the-escape-hatch)). That dependency is the reason the two Decisions cannot be read apart.

Treating unreadable source as drift rather than as an exemption is the same judgement one tier down: an unverifiable body must not be silently superseded.

### Alternatives considered (and rejected)

- **Degrade gracefully on a missing private symbol — log one INFO notice and return.** This is what the plan specified and what the tag shipped. Rejected at `48f9f65d` on the ground above. The rejection retired two tests outright rather than renaming them: `test_apply_no_ops_when_database_failure_symbol_missing` and `test_apply_logs_missing_symbol_notice_only_once`. Their replacements are `test_apply_fails_loudly_when_database_failure_symbol_missing` and `test_apply_fails_loudly_when_upstream_method_signature_changes`.
- **Validate only the signature, not the body.** Rejected at `0d655bde`: a shape-passing body change is exactly the case where the replacement would clobber a working teardown, which is the harm the patch exists to prevent.
- **Pin a Django version range instead of body text.** Rejected: a version range is a proxy for the body and drifts from it. A patch release can reflow the method inside a "supported" version.

### Changes this Decision underwent

- **`48f9f65d`** captured the original at import, added tiers 1 and 2, and deleted `logger`, `logger.info` and `_missing_symbol_logged` along with both retired tests. Its commit subject is about the type registry and never mentions this file: **the cause is an inference** from the diff plus the successor commit's body two days later ("shape-passing body drift now refuses to install instead of clobbering a working teardown"), which is `0d655bde`'s sentence, not this commit's.
- **`0d655bde`** added tier 3 and the `except (OSError, TypeError)` drift arm.
- **`18550f5d`** changed `_validate_upstream_shape`'s return type from `None` to `str`, so `apply()` could record which audited body was validated.

### Claims this Decision may no longer make

- **"A missing private `_DatabaseFailure` symbol no-ops with one log notice."** There is no logger in the module at HEAD.
- **"Django private-symbol drift does not break package import or app loading."** Half of it survives and half does not: module *import* is still guarded by the `try/except ImportError`, so the package still imports; **app loading is not** — `apply()` raises.
- **"That keeps the rest of the package loadable on future Django versions that break the private symbol."** At HEAD a missing symbol means the app does not boot until the consumer sets `{"django": False}`.
- **That the log-once sentinel was a planned deliverable.** It was not, in either direction: it post-dates the recovered plan's last content-bearing write, and it was retired six weeks later. What the plan promised was the INFO-notice no-op; `744fd28d` built the mechanism that made an already-shipped claim true, and `48f9f65d` deleted both.

## Decision 5 — Two audited upstream bodies, discriminated by the validated source

Spec text: [Decision 5][spec-024-d5]. Contract that stays: exactly two audited bodies, discriminated by the validated source, widened only by an audit.

### Derivation

The class-attribute body covers Django `5.2.16` - `6.0.x` and the connection-feature body covers `6.1`. Both resolve to the same four `(name, operation)` pairs, so one replacement can serve both provided the *read* differs.

**Why the validated body and not `hasattr(cls, …)`, stated as mechanism because it is the part that gets "simplified" back:** a Django `6.1` subclass may still declare its own `_disallowed_connection_methods`, but upstream's `_add_databases_failures` ignores that attribute and wraps the **feature list**. Cleanup must read the same list setup wrote, or the two stop being symmetric and the patch unwraps a list nothing wrapped while leaving the wrapped list in place. **A future contributor who replaces the validated-source comparison with a `hasattr` read reintroduces a known defect that shipped and survived ten days.** The `hasattr` form looks more robust because it reads state off the class instead of a module global; that appearance is the trap.

### Alternatives considered (and rejected)

- **`hasattr(cls, "_disallowed_connection_methods")` as the discriminator.** Shipped at `eb2a1764` and documented there as a *feature* — "the presence of the class attribute is therefore the discriminator, read off `cls` rather than off a Django version number so a subclass that still declares its own list keeps being honoured." Named as a **bug** at `18550f5d`, ten days later, for the reason above. The docstring sentence was inverted in place.
- **Branch on a Django version number.** Rejected throughout: the body, not the version, is what the patch supersedes, and a version check would pass on a patch release that reflowed the method.
- **Keep a single pinned body and raise the floor when it changes.** Rejected at `eb2a1764` as the thing that had just gone wrong: a single pin plus a new Django is an outage, and the fix is an audited set, not a narrower support range.

### Changes this Decision underwent

- **`0d655bde`** introduced the pin as one constant holding a single body.
- **`eb2a1764`** widened it to `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`, a tuple of two, after Django `6.1` deleted `SimpleTestCase._disallowed_connection_methods` and moved the pairs onto the per-connection feature flag; the single pin matched neither shape, so `ready()` raised and the package refused to boot on `6.1`. The same commit added `_disallowed_connection_methods` and the `WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP` rule with its three-part obligation.
- **`18550f5d`** replaced the discriminator and added a fail-closed `RuntimeError` for the case where no body has been validated at all.
- **This cycle's rename-rot slice** repaired the one casualty of `eb2a1764`'s rename: `django_strawberry_framework/_strawberry_patches.py`'s module docstring still cited the retired single-body constant. `AGENTS.md` #"Source refs in docs and code comments use symbol paths never line numbers" binds the sweep to the change that renames the symbol, so the repair was card 024's own.

### Claims this Decision may no longer make

- **"The patch pins *the* superseded upstream body."** It pins a set, and widening the set is an audit rather than a version bump.
- **"A subclass that still declares its own list keeps being honoured."** Stated as a feature at `eb2a1764`; it is a defect.
- **"The negative regression test pins the upstream method shape verbatim, so a Django upgrade that changes the iteration source will fail the negative test visibly."** The predicted event happened and the signal came from somewhere else entirely — the body pin made `ready()` raise. See [Decision 10](#decision-10--coverage-lives-in-the-package-test-tree) for what the negative test now pins instead.

## Decision 6 — `APPLY_UPSTREAM_PATCHES` is the escape hatch

Spec text: [Decision 6][spec-024-d6]. Contract that stays: an opt-out defaulting to on, in a bool or a per-dependency mapping, read as `apply()`'s first statement.

### The reversal this Decision records

The original decision was **no settings escape hatch at all**, on two grounds: [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" forbids preemptive keys, and — the substantive half — *"the patch is strictly defensive; it never makes Django's behaviour worse, so there's no foreseeable reason to opt out."*

**The second ground collapsed.** It stopped being true the moment [Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers) landed: a patch that can raise at `AppConfig.ready` can absolutely make Django's behaviour worse, and `eb2a1764` records exactly that outcome — the package refused to boot on Django `6.1`. From that point the hatch is not optional polish; it is the documented recovery path for a consumer who upgraded Django ahead of the package. The first ground never actually argued against the key either — it says *when* to add one, and the feature that needed it had by then landed.

That coupling is why the gate is `apply()`'s **first** statement, ahead of validation, and why `tests/test_django_patches.py::test_django_dependency_opt_out_silences_drifted_pin_abort` pins the pairing end to end rather than the two features separately. A gate placed after validation would be unreachable in the situation it exists for.

### Alternatives considered (and rejected)

- **No key; a consumer who needs to disable the patch files a card.** The original decision. Rejected once the patch could refuse to boot: a card is not a remedy on the timescale of a blocked deployment.
- **A bool only.** Rejected at `0d655bde`: this is a *test-only* patch sitting beside two *production* request-hardening patches, so a consumer disabling this one should not lose those. The per-dependency mapping exists to make the blast radius one module.
- **Coerce loose values (`"false"`, `0`).** Rejected in `django_strawberry_framework/conf.py::upstream_patches_enabled`: a `"false"` string is truthy and would silently *enable* the patches — the failure direction that produces a false sense of having opted out. Every off-contract shape raises `ConfigurationError`, and the whole mapping is validated on every read so a typo'd dependency name fails at the first gate regardless of which patch module reads first.

### Changes this Decision underwent

- **`c7cb5f5c`** added the global bool gate as `apply()`'s first statement, driven by a sibling card's two new patch modules rather than by anything in this surface.
- **`a62d6dca` / `0d655bde`** (same day) added the per-dependency mapping, moved the call to `upstream_patches_enabled("django")`, and rewrote all three drift messages to name `APPLY_UPSTREAM_PATCHES = {"django": False}` so a failure carries its own remedy.

### Claims this Decision may no longer make

- **"No `DJANGO_STRAWBERRY_FRAMEWORK` settings escape hatch … there's no foreseeable reason to opt out."** Reversed in both halves.
- **"The patch is strictly defensive - it never makes Django's behaviour worse."** The sentence survives in `django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures`'s docstring, where it is still true — it describes the *replacement body's* behaviour when the patch is installed, and that body still leaves a foreign replacement untouched. It is false of `apply()`, and it may no longer be used to argue that no opt-out is needed.
- **"Consumers get the hardening … no settings key."** The correct statement is "no settings key **required**": no key is needed to get the patch, and one exists to refuse it.

## Decision 7 — Idempotent, self-healing, and reload-safe

Spec text: [Decision 7][spec-024-d7]. Contract that stays: an actual-state check, not a flag; plus a descriptor capture that survives an in-process reload.

### Derivation

`ready()` fires more than once under some Django test runners, and a third party can revert the class attribute between calls. Reading actual state satisfies both cases with one mechanism; a flag satisfies only the first while its docstring implies both.

Reload safety is a second-order consequence of [Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers): once the module validates a captured "original", the capture itself becomes a correctness surface. `importlib.reload()` re-executes the module while `SimpleTestCase` still points at the previous replacement, so a naive re-capture stores the package's own function as the original, and tier 3 then compares the package's source against the audited set and aborts against its own code. The owner stamp is what breaks that chain.

### Alternatives considered (and rejected)

- **A `_PATCH_APPLIED` module-global bool.** Shipped at `300e2811`, rejected at `7014125a`. Its own docstring promised "re-entrant calls are no-ops", which was true, but the flag silently also meant "and never re-installs after a third party reverts". The docstring promised a contract the code did not keep.
- **Refuse to support reload and document it.** Rejected: the failure mode is not a missing feature but a *false* upstream-drift abort against the package's own source, which is indistinguishable from real drift for whoever hits it.

### Changes this Decision underwent

- **`7014125a`** deleted the flag and introduced `_patch_is_installed()`, comparing `__func__` identity out of `SimpleTestCase.__dict__`.
- **`e82df83d`** added coverage for the `installed is None` branch.
- **`18550f5d`** added `_PATCH_OWNER_ATTRIBUTE`, `_PATCH_ORIGINAL_ATTRIBUTE`, `_PATCH_OWNER` and `_captured_upstream_descriptor`, with the two `setattr` stamps applied at module scope after the replacement is defined. Note precisely what each name is: two are attribute-name constants, and `_PATCH_OWNER` is the owner **value** the first of them is compared against; `_captured_upstream_descriptor` returns the second's value when the comparison holds.

### Claims this Decision may no longer make

- **"Idempotent: re-entrant calls are no-ops"** as the whole contract. The contract is idempotent **and** self-healing.

## Decision 8 — The wrap-time half degrades where the unwrap-time half aborts

Spec text: [Decision 8][spec-024-d8]. Contract that stays: `True` on install, `False` on decline, `TypeError` on a non-callable wrapper, and install-on-drift.

### Derivation

The two halves sit at the two lifecycle sites this package can influence, and the wrap-time check is the cheaper of the two: declining costs one predicate and installs nothing. It is unavoidably advisory — the package cannot make third-party wrappers call it — which is why the unwrap-time half exists and is not optional.

**Why the fail-loud reversal deliberately stopped at the module boundary.** `apply()` runs inside `AppConfig.ready`, where raising is a decision about whether the *package* should install a protection it cannot verify. `safe_wrap_connection_method` is reached through the public `django_strawberry_framework.testing` import, where the same posture would make a consumer's import crash on a Django private-symbol move. The helper instead reads a missing `_DatabaseFailure` as "no Django wrapper is present, so the slot is free", installs, and returns `True`. `tests/testing/test_wrap.py::test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing` pins it, so the asymmetry is a contract rather than an oversight. It is also barely reachable in practice: with the Django patch enabled, `ready()` has already refused to boot.

### Alternatives considered (and rejected)

- **Follow `apply()` into fail-loud.** Rejected on the boundary argument above.
- **Restore the original method on the consumer's behalf.** Rejected: restoration needs the original, the ordering, and the teardown hook, none of which the helper owns. The docstring carries the worked `setUp` / `tearDown` shape instead, and the unwrap-time backstop makes omitting it non-fatal.
- **Interpolate the offending object into the `TypeError`.** Shipped at `7014125a`, rejected at `f7fbead4`: the object is consumer-supplied and a `__repr__` that raises would replace the intended `TypeError` with whatever it raised. The diagnostic loses the object's identity deliberately.

### Changes this Decision underwent

- **`61973f8d`** shipped the helper with 4 tests.
- **`7014125a`** added the non-callable `TypeError` guard and the private-symbol-drift fallback, taking the file to 6 tests. Both of the two added tests matter for attribution: one is the plan's own fifth Phase-4 clause, and one is beyond plan.
- **`744fd28d`** corrected the `Raises:` example, which had used `connection.cursor` — a bound method, and therefore callable, so the example contradicted itself — in place of `connection.cursor()`.
- **`b8a8a6e0`** folded an RST subsection heading into a bold run and added the example's missing `TransactionTestCase` import, which had made the block non-runnable as written.
- **`f7fbead4`** removed the interpolation. 6 -> 7 tests.

### Claims this Decision may no longer make

- **That the `TypeError` names the offending object.** A consumer parsing the message for the wrapper's repr gets less at HEAD, deliberately.

## Decision 9 — The helper is a submodule export only

Spec text: [Decision 9][spec-024-d9]. Contract that stays: exported from `django_strawberry_framework.testing`, never from the package root.

### Derivation

The package's general posture is zero public-export change per card. A public surface is nonetheless correct here, and the recovered plan argued it well: the sibling multi-database card needed no new symbols because the cooperation it pinned already existed in source, whereas Trac #37064 is a bug in Django and this package's guard is the first defensive layer — the value-add *is* new behaviour. Shipping only the auto-applied unwrap patch protects every consumer but gives them nothing to write defensive `setUp` code against. The submodule path is the compromise: opt-in by import, invisible to anyone who does not want it.

### Alternatives considered (and rejected)

- **Re-export from `django_strawberry_framework/__init__.py`.** Rejected: a test-only helper does not belong on the package's front page, and the root `__all__` is the package's whole public surface.
- **Ship no public symbol at all.** Rejected per the derivation: it leaves the wrap-time half unreachable by consumers.
- **The subpackage name `test`.** Rejected at `e145ba36`: `django_strawberry_framework.test` shadows the stdlib-adjacent `test` name and collides with collection of a package so named.

### Changes this Decision underwent

- **`e145ba36`** renamed `django_strawberry_framework/test/` to `testing/` and `tests/test/` to `tests/testing/`, rewriting the documented consumer import path in every docstring. A consumer following the `0.0.7` docstring's `from django_strawberry_framework.test import safe_wrap_connection_method` breaks; the rename is post-tag.
- The `testing` subpackage later grew a whole test-client family under a different card. That is not this card's surface and this card's contract does not describe it.

### Claims this Decision may no longer make

- **That the public import path is `django_strawberry_framework.test`**, or that the package's own coverage for the helper is at `tests/test/test_wrap.py`. Both paths are dead.
- **That `__all__` in `django_strawberry_framework/__init__.py` is "unchanged"** without qualification. What this card owns is the narrower true statement: no symbol from this work ever entered the root `__all__`, at the ship or since. That tuple is the package's whole public surface and moves every release, so a count of its members written into a permanent spec by a card that does not own it would be rot with a verification date on it — which is why the spec states the claim without one.

## Decision 10 — Coverage lives in the package test tree

Spec text: [Decision 10][spec-024-d10]. Contract that stays: `tests/` only, no live tier, no sharded gate.

### Derivation

The failure is Django test-class setup/teardown behaviour and is not reachable through a live `/graphql/` query, so the [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" preference does not apply and its documented fallback does. The bug sits below the GraphQL API layer; the example project stays useful as fixtures.

No `FAKESHOP_SHARDED=1` gate, because the hardening protects every consumer rather than only multi-database ones. Running the same focused scope under the sharded mode is still worthwhile — it is the only mode configuring more than one alias, which is the condition upstream wraps disallowed methods for — but it is an extra run of the same tests, not a separate suite.

### Alternatives considered (and rejected)

- **Live `/graphql/` coverage in `examples/fakeshop/test_query/`.** Rejected: no query can reach `tearDownClass` of a Django test case.
- **A hardcoded copy of Django's upstream body inside the negative test.** Shipped, rejected at `0d655bde`. The negative test's job is to prove the bug is real at the installed Django *and to stop proving it* when upstream fixes it — a retirement signal. A hardcoded copy would keep crashing no matter what the installed Django ships, so it could never deliver that signal. The test now reverts to the live import-time capture and first asserts the captured descriptor's `__func__.__module__` is `django.test.testcases`, so its premise is checked before its conclusion.

### Changes this Decision underwent

- **`0d655bde`** switched the negative test to the live capture.
- **`136c5476`** added `tests/test_apps.py::test_ready_dispatches_all_three_patch_appliers_and_refires_safely`, because each module's installed-at-collection assertion was masked by earlier direct `apply()` calls on the same worker — a dropped dispatch line could have passed the gate.
- **`18550f5d`** added the reload test, which reloads each patch module twice so the contract holds for a reload of a reload.

### Claims this Decision may no longer make

- **That the negative test holds "a verbatim copy of Django's upstream body".** It holds the live capture.
- **"No real Django connection state is mutated for these tests."** False at HEAD and **false at the ship commit too** — `300e2811`'s own happy-path test assigned `connection.cursor`. The claim was never true; the part of the decision that does hold is the sentinel technique (`_DatabaseFailure(sentinel, …)` for the happy path, a plain callable with no `.wrapped` for the bug path). At HEAD the mutation is wider still: the connection-feature test writes `disallowed_simple_test_case_connection_methods` on every alias and deletes it in `finally`.
- **That this card owns 31 tests, three of them the `ready()` tests in `tests/test_apps.py`.** It owns
  **28** — `tests/test_django_patches.py` (21) and `tests/testing/test_wrap.py` (7). All eight of
  `tests/test_apps.py` belong to [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021]. The reconciliation that
  produced the 31 corrected an earlier 36 by separating run scope from ownership, then stopped one step
  short: it asked "population of what?" of the five `AppConfig`-shape tests and not of the three it kept.
  The three are the sibling card's because each asserts a contract over **all three** patch appliers —
  `_django_patches`, `_strawberry_patches`, `_cross_web_patches` — while this card ships only the first;
  the dispatcher contract they pin is specified at that spec's `#"Decision 4"`. This card's commits
  `300e2811`, `136c5476` and `18550f5d` authored them, which is provenance, not ownership. Under 28 the
  focused-run arithmetic also closes without overlap: 28 owned + 8 sibling-owned = the 36 a run collects.
- **"The repo-root `conftest.py` workaround has been deleted."** A definition-of-done item satisfiable only vacuously: `git log --all --oneline --diff-filter=D -- conftest.py tests/conftest.py` is **empty** — no `conftest.py` has ever been deleted in this repository, on any ref. The workaround lived in a *different* repository. The repo-root `conftest.py` that exists today was created at `57cbd32a` (2026-07-07), six weeks after this card shipped, and belongs to the Postgres tier. Recorded so a future reader does not read it as the workaround's survival.

## Decision 11 — Joint `0.0.7` cut

Spec text: [Decision 11][spec-024-d11]. Contract that stays: this card ships in the joint `0.0.7` cut.

### Alternatives considered (and rejected)

- **A separate `0.0.8` cut for this card.** The recovered plan left the choice open as a maintainer decision. Rejected in favour of the joint cut under [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut]; the card shipped as one of seven in `0.0.7` on 2026-05-27.

### Changes this Decision underwent

- None. The open question closed once and stayed closed.

## Claims the spec may no longer make

Consolidated so a reader can see at a glance which statements were once asserted about this card and are now absent from the spec. Each is recorded in full under the Decision it belongs to.

1. The patch installs on `TransactionTestCase` ([Decision 2](#decision-2--the-patch-installs-on-simpletestcase)).
2. A missing `_DatabaseFailure` no-ops with one log notice, and private-symbol drift does not break app loading ([Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers)).
3. The patch pins *the* superseded upstream body; a subclass declaring its own list keeps being honoured; the negative test is what signals a needed patch update ([Decision 5](#decision-5--two-audited-upstream-bodies-discriminated-by-the-validated-source)).
4. There is no settings escape hatch and no foreseeable reason to opt out; consumers need "no settings key" ([Decision 6](#decision-6--apply_upstream_patches-is-the-escape-hatch)).
5. Idempotence is the whole of the re-entrancy contract ([Decision 7](#decision-7--idempotent-self-healing-and-reload-safe)).
6. The `TypeError` names the offending object ([Decision 8](#decision-8--the-wrap-time-half-degrades-where-the-unwrap-time-half-aborts)).
7. The public import path is `django_strawberry_framework.test`; the root `__all__` is unqualifiedly unchanged ([Decision 9](#decision-9--the-helper-is-a-submodule-export-only)).
8. The replacement is a verbatim copy of upstream's body ([Decision 3](#decision-3--the-replacement-reimplements-the-loop-behind-one-guard)); the negative test holds a verbatim copy; no real connection state is mutated by the tests; the repo-root `conftest.py` workaround was deleted ([Decision 10](#decision-10--coverage-lives-in-the-package-test-tree)).
9. The patch is "~30 lines of code with a 30-line rationale docstring", and additional patches land as more functions in the same module ([Decision 1](#decision-1--a-private-patch-module-per-dependency-applied-from-ready)).
10. This card owns 31 tests, three of them in `tests/test_apps.py` ([Decision 10](#decision-10--coverage-lives-in-the-package-test-tree)).

## Verified against the shipped code

The reconstruction was checked against HEAD rather than against the recovered documents alone. Two independent audit cohorts, working from disjoint angles and neither reading the other's record, both concluded **no code gap**: nothing planned for card `DONE-024-0.0.7` is absent from HEAD without a deliberate, tested retirement. All nine definition-of-done items from the recovered plan are accounted for, all fifteen named regression tests are located at HEAD (two of them with their assertions deliberately inverted, both recorded above), all five recovered decisions still describe HEAD except the escape hatch — reversed by design — and the never-true connection-state claim, all four recovered risks are closed or explicitly superseded, and nothing from the recovered out-of-scope list was built under this card.

The floor was executed rather than asserted: the focused scope runs green at Django `5.2.16` on Python `3.10` with strawberry-graphql `0.316.0` in an isolated venv, where the class-attribute audited body is the validated one — the shape covering most of the supported range, and one that a newer environment cannot reach.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-020-decision-10--joint-007-cut]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-024]: ../spec-024-django_trac_37064_hardening-0_0_7.md
[spec-024-d1]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-1--a-private-patch-module-per-dependency-applied-from-ready
[spec-024-d10]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-10--coverage-lives-in-the-package-test-tree
[spec-024-d11]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-11--joint-007-cut
[spec-024-d2]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-2--the-patch-installs-on-simpletestcase
[spec-024-d3]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-3--the-replacement-reimplements-the-loop-behind-one-guard
[spec-024-d4]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-4--fail-closed-upstream-validation-in-three-tiers
[spec-024-d5]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-5--two-audited-upstream-bodies-discriminated-by-the-validated-source
[spec-024-d6]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-6--apply_upstream_patches-is-the-escape-hatch
[spec-024-d7]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-7--idempotent-self-healing-and-reload-safe
[spec-024-d8]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-8--the-wrap-time-half-degrades-where-the-unwrap-time-half-aborts
[spec-024-d9]: ../spec-024-django_trac_37064_hardening-0_0_7.md#decision-9--the-helper-is-a-submodule-export-only
[spec-024-terms]: spec-024-django_trac_37064_hardening-0_0_7-terms.csv

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
