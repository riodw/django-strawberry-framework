# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- Defer until a third caller for the rollback shape appears: extract a private `_rollback_register(model, type_cls, pre_primary)` helper from the rollback block at `registry.py:286-296`. Today it's only called from `register_with_definition`'s exception handler and would still need to share `appended` context, so the gain is small at N=1.

## High:

None.

## Medium:

### `_already_registered` docstring overstates its coverage

The helper's docstring (`registry.py:67-72`) claims it centralizes "three mutator collision messages (``register`` forward, ``register`` reverse, ``register_enum``)". In practice the helper is called only twice — at `registry.py:115` (reverse-collision: same `type_cls`, different model) and `registry.py:365` (`register_enum` collision). The two "forward" collision sites in `register` (primary-flip on idempotent re-register at `registry.py:121-123`, duplicate-primary at `registry.py:128-130`) and the `register_definition` collision at `registry.py:261` each inline their own `ConfigurationError(...)` f-string. Worker-1 memory carried this forward from the `rev-exceptions.md` pass: "check if `_already_registered` is the only canonical builder or whether other error message templates have drifted". They have drifted. The phrasings are not bugs — every one is test-pinned by `match=` substring at `tests/test_registry.py:70,144,203,761,775` — but the docstring's claim of three-site coverage is wrong, and the helper's design assumes a `{label}` slot that the primary-related raises can't naturally use ("already registered for ... primary flag cannot be flipped" and "already declared primary as" don't fit the `{name} is already registered {label} {existing_name}` template). Either widen the helper to accept arbitrary suffix phrasings (overengineered for four sites) or correct the docstring to describe what the helper actually centralizes (two sites: cross-model reverse-collision and enum-key collision). The simpler, recommended fix is the docstring correction.

```django_strawberry_framework/registry.py:65:73
@staticmethod
def _already_registered(label: str, name: str, existing_name: str) -> ConfigurationError:
    """Build the canonical "already registered" ``ConfigurationError``.

    Centralizes the phrasing so the three mutator collision messages
    (``register`` forward, ``register`` reverse, ``register_enum``)
    stay grep-stable for tests and consumer error matching.
    """
    return ConfigurationError(f"{name} is already registered {label} {existing_name}")
```

### `unregister` docstring promises no-op but `_check_mutable` raises first

The `unregister` docstring (`registry.py:137-160`) advertises "No-op when ``type_cls`` is not registered: test teardown often wants 'clean up if present' semantics, and consumers that need strictness can layer a check on top." But the very first line of the body is `self._check_mutable()` (`registry.py:161`), which raises `ConfigurationError` after `mark_finalized` regardless of whether `type_cls` is registered. So a test that calls `unregister(SomeUnregisteredType)` post-finalize gets a `ConfigurationError` — not the documented no-op. The docstring acknowledges the finalize guard in its second paragraph ("Honours ``_check_mutable()``"), but the "No-op when not registered" sentence is unconditional and the order matters: for a not-registered type, the `_check_mutable` guard fires *before* the `if model is None: return` early-exit at `registry.py:162-164`. This is brittle docstring/behavior drift, not a correctness bug — the production callers in `types/base.py` never call `unregister`, and the tests at `tests/test_registry.py:604` exercise the post-finalize raise on the *registered*-type path. But a consumer reading the docstring at face value would assume safe idempotent cleanup is available post-finalize for unknown classes, which it is not. Recommend tightening the docstring to make the order explicit: "No-op when ``type_cls`` is not registered (unless the registry has been finalized; the finalize guard fires before the registration check)." No source-behavior change required.

```django_strawberry_framework/registry.py:137:164
def unregister(self, type_cls: type) -> None:
    """Remove all traces of ``type_cls`` from the registry.
    ...
    consumers that need strictness can layer a check on top.

    Honours ``_check_mutable()``: after ``finalize_django_types()`` the
    finalized registry is the runtime lookup source ...
    """
    self._check_mutable()
    model = self._models.pop(type_cls, None)
    if model is None:
        return
```

## Low:

### Rollback in `register_with_definition` duplicates `unregister`'s inverse mutations

The rollback block at `registry.py:286-296` manually undoes the state added by the failed `register` call (drop `type_cls` from `_types[model]`, pop empty list, pop `_models[type_cls]`, restore `_primaries`). Most of this overlaps with what `unregister` does (`registry.py:162-175`), and a future maintainer who tightens `register` (e.g., a new lookaside dict) will have to update both the registration site and this manual rollback. `unregister` cannot be called directly because it would also pop `_definitions[type_cls]` (which was never added on the failure path; harmless) and rebuild `_pending` (no-op; this code path doesn't add pending records), but more importantly it can't restore `pre_primary` — `unregister` clears the primary unconditionally. So a literal `self.unregister(type_cls); if pre_primary is not None: self._primaries[model] = pre_primary` would work but introduces a double-walk of `_pending` and bypasses `_check_mutable` issues. The current inline rollback is correct; the risk is purely maintenance drift if `register` ever gains a new side-effect that this rollback forgets to undo. Tests at `tests/test_registry.py:660-878` lock the post-rollback state for the current shape. Suggested: a `# When register grows a new side effect, mirror it here.` anchor comment, or extract a tiny private `_rollback_register(model, type_cls, pre_primary)` helper to make the inverse-of-register contract one local edit.

```django_strawberry_framework/registry.py:282:297
pre_primary = self._primaries.get(model)
appended = self.register(model, type_cls, primary=primary)
try:
    self.register_definition(type_cls, definition)
except Exception:
    if appended:
        types = self._types.get(model, [])
        types.remove(type_cls)
        if not types:
            self._types.pop(model, None)
        self._models.pop(type_cls, None)
        if pre_primary is None:
            self._primaries.pop(model, None)
        else:
            self._primaries[model] = pre_primary
    raise
```

### `self._types.get(model, [])` default in rollback is dead-defensive

At `registry.py:288` the rollback uses `self._types.get(model, [])` with an empty-list default, then calls `.remove(type_cls)` on the result. When `appended` is `True`, `register` is guaranteed to have set `_types[model]` via `setdefault` at `registry.py:116` and appended `type_cls` at `registry.py:131` — so `model` is always present in `_types` and the `[]` default is unreachable. The unreachable default is harmless (an empty list would fail loudly on `.remove`), but it muddies the lock-step invariant the comment at `registry.py:165-167` describes for the symmetric path in `unregister`. Recommend `self._types[model]` (bare subscript) to mirror the comment's invariant. Trivial polish.

```django_strawberry_framework/registry.py:288:289
types = self._types.get(model, [])
types.remove(type_cls)
```

### `register_definition` collision phrasing diverges from helper

`register_definition` raises with an inline message `"{type_cls.__name__} already has a registered DjangoTypeDefinition"` at `registry.py:261`. This is a fourth distinct "already registered" phrasing in the file (alongside `_already_registered`'s template, the primary-flip phrasing at `registry.py:121-123`, and the duplicate-primary phrasing at `registry.py:128-130`). It doesn't fit the helper's three-argument shape, and tests at `tests/test_registry.py:203,675,801,836,858,878` pin the current substring. Not actionable as a fix; flagged for the project-level pass to confirm the registry's "already registered" surface is intentionally pluralized rather than collapsed.

```django_strawberry_framework/registry.py:258:262
self._check_mutable()
existing = self._definitions.get(type_cls)
if existing is not None and existing is not definition:
    raise ConfigurationError(f"{type_cls.__name__} already has a registered DjangoTypeDefinition")
self._definitions[type_cls] = definition
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The module sits at the bottom of the internal dependency graph: it imports only `collections.abc`, `enum`, `typing`, `django.db.models`, and `.exceptions.ConfigurationError` (`registry.py:16-24`). `TYPE_CHECKING`-guarded imports of `DjangoTypeDefinition` and `PendingRelation` (`registry.py:26-28`) avoid the import cycle with `types/definition.py` and `types/relations.py`. The canonical "already registered" error builder `_already_registered` (`registry.py:66-73`) is the only error-message helper in the file and is the helper noted in the `rev-exceptions.md` DRY entry; every raising site in the registry uses either this helper or an inline `ConfigurationError(...)` with a phrasing that the test suite pins by `match=` substring (`tests/test_registry.py:70,144,203,761,775,801`). Consumers of the singleton `registry` are constrained to the public surface: `types/base.py:153,237,239`, `types/converters.py:270,293,343`, `types/finalizer.py:82-168`, `types/resolvers.py:165`, `optimizer/extension.py:351,417,655-669`, `optimizer/walker.py:104,116,226`. None of those sites reach into `_types`/`_primaries`/`_models`/`_definitions`/`_pending`/`_enums` directly — every read goes through `get`, `model_for_type`, `iter_types`, `primary_for`, `types_for`, `models_with_multiple_types`, `get_definition`, `iter_definitions`, `iter_pending_relations`, `get_enum`, or `is_finalized`, which is the cross-file boundary the docstrings advertise. The `register_with_definition` atomic wrapper (`registry.py:264-297`) is the only call site of the public `register` from inside the module — outside callers always go through `register_with_definition`.
- **New helpers considered.** The two adjacent `if not types: self._types.pop(model, None)` cleanup branches at `registry.py:170-171` and `registry.py:290-291` are the same "drop empty list" idiom, but extracting a one-liner `_drop_if_empty(model)` helper would obscure the existing inline comment at `registry.py:165-167` that justifies the lock-step invariant. Keep them inline.
- **Duplication risk in the current file.** The `_already_registered` docstring at `registry.py:66-73` advertises "three mutator collision messages (``register`` forward, ``register`` reverse, ``register_enum``)" but only two raise sites call the helper (`registry.py:115` reverse-collision in `register`; `registry.py:365` `register_enum`). The "forward" collision in `register` is actually two inline f-strings — the primary-flip on idempotent re-register at `registry.py:121-123` and the duplicate-primary collision at `registry.py:128-130` — neither routes through the helper. The `register_definition` collision at `registry.py:261` is a fourth distinct "already registered" phrasing inline. These are not bugs (every phrasing is test-pinned by substring) but they drift from the helper's own contract claim. Repeated-string-literal scan from the helper found no shared literals across raise sites; the helper template `"{name} is already registered {label} {existing_name}"` and the three inline phrasings produce four grep-stable substrings ("already registered against", "already registered as", "already registered for ... primary flag cannot be flipped", "is already declared primary as", "already has a registered DjangoTypeDefinition") that tests at `tests/test_registry.py:70,144,761,775,203` lock in. Two adjacent `if not types: self._types.pop(...)` blocks (`registry.py:170-171`, `registry.py:290-291`) are intentional duplication of the lock-step invariant. The cross-file "already registered" phrasing question is tracked in the Medium section and forwarded to the project-pass artifact.

### Other positives

- **Static helper coverage matches scope.** The helper ran cleanly; the only control-flow hotspot is `register` (61 lines / 7 branches at `registry.py:75`), and every branch has a dedicated test (`tests/test_registry.py:42-995`). The Django/ORM marker table is dominated by docstring mentions of `DjangoType` and `_meta` — there is no live ORM call in this module, which matches the registry-as-pure-dict-store role advertised in `AGENTS.md`. No repeated string literals; no TODO comments.
- **Thread/process safety is explicitly addressed.** The class docstring at `registry.py:32-39` documents the unlocked-but-safe invariant ("every production-path mutation runs at import time from ``DjangoType.__init_subclass__``"), and `_check_mutable` at `registry.py:50-63` enforces a defense-in-depth guard that fires before any mutator. Every mutator that writes to internal state calls `_check_mutable` first (`register`, `unregister`, `register_definition`, `register_with_definition` via `register`, `add_pending_relation`, `discard_pending`, `register_enum`). `clear` intentionally does not call `_check_mutable` so test teardown can reset a finalized registry.
- **Key-shape contract is consistent.** Every model-keyed mapping (`_types`, `_primaries`, `_enums` outer key) uses the model **class** (`type[models.Model]`) — no `_meta.label` string keys, no app-label tuples, no ContentType detours. This matches the optimizer/extension consumers at `optimizer/extension.py:417,669` and `optimizer/walker.py:226` which pass model classes directly. The single composite key is `_enums: dict[tuple[type[models.Model], str], type[Enum]]` (`registry.py:45`), which `types/converters.py:270,293` reads/writes through the public `get_enum`/`register_enum` boundary.
- **TYPE_CHECKING-guarded imports avoid the cycle.** `DjangoTypeDefinition` and `PendingRelation` are imported under `if TYPE_CHECKING` (`registry.py:26-28`) because both modules import from this one; the runtime annotations resolve under `from __future__ import annotations` (`registry.py:16`). No circular-import risk, no import-time side effects (the singleton at `registry.py:396` is a parameterless constructor that only mutates a dict-shaped instance).
- **Public surface is well-segmented.** Reads and writes are paired through dedicated public methods (`get`/`primary_for`/`types_for`/`models_with_multiple_types` for the type registry; `get_definition`/`iter_definitions` for definitions; `iter_pending_relations`/`add_pending_relation`/`discard_pending` for pending; `get_enum`/`register_enum` for enums; `is_finalized`/`mark_finalized`/`clear` for lifecycle). Every public method has a docstring describing the contract. `unregister` is the only public method that crosses internal seams in one call, and its docstring at `registry.py:138-160` explicitly enumerates them.
- **`register_with_definition` rollback semantics are tight where it counts.** The atomic wrapper at `registry.py:264-297` correctly snapshots `pre_primary` before `register`, and the rollback at `registry.py:286-296` distinguishes "we added the type" (`appended=True`) from "the type was already present and only the definition was new" (`appended=False`). The idempotent-re-register survival case is locked by `tests/test_registry.py:846`. The pre-existing-primary restoration is locked by `tests/test_registry.py:811`. The rollback never overshoots into pre-existing state.

### Summary

`registry.py` is the bottom of the package's internal dependency graph and the only writable singleton; the file's contract surface is broad (24 methods across the type/definition/pending/enum/lifecycle quadrants) but every method has a docstring and a dedicated test. No High findings. Two Medium findings are pure docstring drift — the `_already_registered` helper claims more centralization than it delivers, and `unregister`'s "no-op when not registered" sentence skips over the `_check_mutable` guard that runs first. Three Low findings are localized polish around the `register_with_definition` rollback (manual inverse of `register`'s mutations, an unreachable `[]` default, and a fourth distinct "already registered" phrasing in `register_definition`). The cross-file "already registered" phrasing question is forwarded to the project-pass artifact for a single review of whether the four pluralized phrasings should remain or collapse. Thread/process safety, key-shape consistency, TYPE_CHECKING cycle avoidance, and rollback semantics are all solid.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/registry.py:288` — one-line simplification of the rollback's `_types` lookup. Changed `self._types.get(model, [])` to `self._types[model]`. On this path `appended` is `True`, which means `register` ran the `setdefault(model, [])` at `registry.py:116` and `existing_types.append(type_cls)` at `registry.py:131` before `register_definition` was attempted, so `_types[model]` is guaranteed present. The bare subscript mirrors the symmetric path in `unregister` at `registry.py:168-171`, which the inline lock-step-invariant comment at `registry.py:165-167` documents. The previously unreachable `[]` default no longer masks the invariant. No other source changes; no test changes (existing rollback coverage at `tests/test_registry.py:660-878` already pins the behavior and the simplification is semantically equivalent under all reachable inputs).

### Tests added or updated

- None. The simplification is semantically equivalent on every reachable input. `tests/test_registry.py:660-878` already covers the rollback paths (`appended=True` definition-collision, idempotent-re-register survival, pre-existing-primary restoration, post-rollback empty-list cleanup); no behavior change to pin.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed; ruff prints the standing `COM812` + formatter co-existence warning, which is expected and not a finding from this edit).
- No `pytest` run per `START.md` standing rule (formatting only after edits).

### Notes for Worker 3

- This is the **logic pass only**. The artifact lists 0 High, 2 Medium, 3 Low.
- **Medium 1** (`_already_registered` docstring overstates coverage) — docstring-only; deferred to the comment pass.
- **Medium 2** (`unregister` docstring promises no-op but `_check_mutable` raises first) — docstring-only; deferred to the comment pass.
- **Low 1** (rollback duplicates `unregister`'s inverse mutations) — Worker 1 framed this as maintenance-drift insurance, not a behavior bug. The anchor-comment option is chosen over extracting `_rollback_register`; the anchor comment itself is a comment, not logic, and is deferred to the comment pass. No logic change in this pass.
- **Low 2** (dead-defensive `self._types.get(model, [])` default) — implemented in this pass as the one-line simplification described above. This is the only source change in the logic pass.
- **Low 3** (`register_definition` collision phrasing diverges from helper) — forwarded by Worker 1 to the project pass per the artifact; not actionable here.
- No shadow file was used.
- The diff is one line: `self._types.get(model, [])` → `self._types[model]` at `registry.py:288`.

---

## Verification (Worker 3)

### Logic verification outcome

- **High** — None. Accepted.
- **Medium 1** (`_already_registered` docstring overstates coverage) — docstring-only; deferred to the comment pass. Accepted.
- **Medium 2** (`unregister` docstring promises no-op but `_check_mutable` raises first) — docstring-only; deferred to the comment pass. Accepted.
- **Low 1** (rollback duplicates `unregister`'s inverse mutations) — deferred to the comment pass with the anchor-comment choice (no helper extraction). Accepted.
- **Low 2** (dead-defensive `self._types.get(model, [])` default) — applied at `registry.py:288` as the bare subscript `self._types[model]`. Safety argument confirmed by walking `register` at `registry.py:75-135`: when the rollback's `if appended:` branch fires, `register` returned `True`, which means both `self._types.setdefault(model, [])` (line 116) and `existing_types.append(type_cls)` (line 131) ran in this same synchronous call. So `_types[model]` is guaranteed to exist and to contain `type_cls` at the moment the rollback runs; the `[]` default was unreachable. The unlocked-but-safe invariant documented at `registry.py:32-39` rules out concurrent mutation between the failed `register_definition` and the rollback (single synchronous call). The change mirrors the symmetric bare subscript in `unregister` at `registry.py:168` and the lock-step-invariant comment at `registry.py:165-167`. Cannot KeyError on the rollback path under any reachable input. Accepted.
- **Low 3** (`register_definition` collision phrasing diverges from helper) — forwarded to the project pass. Accepted.

### DRY findings disposition

Worker 1's DRY analysis identified the pluralized "already registered" phrasings as a project-pass topic (Low 3) and noted the two adjacent `if not types: self._types.pop(model, None)` idioms at `registry.py:170-171` and `registry.py:290-291` as intentional inline duplication of the lock-step invariant. Local-file DRY is unchanged after Low 2 — no new code introduced, one defensive default removed. Accepted.

### Temp test verification

None used. The artifact's claim that the simplification is semantically equivalent under all reachable inputs is supported by the call-graph walk above; existing rollback coverage at `tests/test_registry.py:660-878` already pins the behavior, and Low 2 is not a High finding so the High-severity test requirement does not apply.

### Verification outcome

logic accepted; awaiting comment pass

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/registry.py:65-77` — `_already_registered` docstring rewritten to describe its actual coverage. Now names the two cross-key collision sites it centralizes (`register`'s reverse-collision and `register_enum`'s `(model, field_name)` collision) and explicitly calls out the inline `ConfigurationError(...)` raises in `register`'s primary-flip / duplicate-primary branches and in `register_definition` as separate, distinct, test-pinned phrasings.
- `django_strawberry_framework/registry.py:141-168` — `unregister` docstring updated so the `_check_mutable`-then-registration ordering is explicit. The "No-op when not registered" sentence now reads "No-op when ``type_cls`` is not registered AND the registry has not been finalized — the ``_check_mutable()`` guard fires before the registration check, so post-finalize calls raise ``ConfigurationError`` even for unknown types." The trailing "Honours ``_check_mutable()``" paragraph is left intact.
- `django_strawberry_framework/registry.py:295` — anchor comment added directly above the rollback's `if appended:` line: `# Inverse of register's mutations above; mirror any new register side-effect here on rollback.` Kept ≤110 columns (the longer 116-column draft tripped E501 and was shortened).

No logic changes in this pass; the logic pass's one-line simplification at `registry.py:288` (now line 297 in the post-edit file due to expanded docstrings) is untouched.

### Medium 1 disposition

Docstring corrected to describe actual coverage (two sites). The helper no longer claims three-site coverage. Excerpt:

> Centralizes the phrasing for the two cross-key collision sites — ``register``'s reverse-collision (same ``type_cls`` for a different model) and ``register_enum``'s ``(model, field_name)`` collision — so consumer error matching stays grep-stable.

The follow-on sentence explicitly names the divergent inline phrasings so a future reader does not re-derive the same Medium 1 finding.

### Medium 2 disposition

Docstring updated to make the `_check_mutable`-then-registration ordering explicit. A consumer reading the docstring will no longer assume safe idempotent cleanup is available post-finalize for unknown classes; the guard ordering is spelled out. The "Honours ``_check_mutable()``" second paragraph remains intact as additional context.

### Low 1 disposition

Anchor comment added above the rollback block in `register_with_definition` at line 295. No `_rollback_register` helper was extracted — the artifact listed the helper as an alternative, and the chosen disposition was the anchor comment per the Worker 1 / Worker 3 framing of the finding as maintenance-drift insurance.

### Low 3 disposition

Confirmed forwarded to the project pass per the artifact. No edit in this scope.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed; standing `COM812` + formatter co-existence warning is expected). Initial draft of the rollback anchor comment was 116 columns and tripped E501; shortened to 100 columns and re-validated.
- No `pytest` run per `START.md` standing rule.

### Notes for Worker 3

- No shadow file was used.
- No logic changes beyond what the logic pass already verified — this pass is docstrings + one inline anchor comment only.
- The line numbers cited in the rev-registry.md artifact's earlier sections refer to the pre-comment-pass file. Post-comment-pass: the `_already_registered` helper body now spans `registry.py:65-77` (docstring grew from 6 lines to 9), `unregister`'s docstring grew so the method body now starts at `registry.py:169` (was 161), and the rollback anchor comment lives at `registry.py:295` directly above `if appended:` (line 296).

Status: fix-implemented

---

## Iteration log

## Verification (Worker 3, pass 2)

### Comment verification outcome

Each of the three comment/docstring sites accurately reflects the artifact's recommended disposition:

- **Medium 1 (`_already_registered` docstring).** Rewritten at `registry.py:67-76`. No longer claims three sites; correctly cites the two cross-key collision sites it actually centralizes — `register`'s reverse-collision (same `type_cls` for a different model) and `register_enum`'s `(model, field_name)` collision. Verified the two-site claim by grepping the file for `_already_registered(`: exactly two callers — `registry.py:119` in `register` (reverse-collision branch, same `type_cls` against a different model) and `registry.py:374` in `register_enum` (`(model, field_name)` collision). The docstring also names the divergent inline phrasings (primary-flip and duplicate-primary in `register`, plus `register_definition`'s phrasing) so a future maintainer does not re-derive this Medium finding. Google convention; longest line ≤110.
- **Medium 2 (`unregister` docstring).** Updated at `registry.py:142-168`. The "No-op when ``type_cls`` is not registered" sentence is now explicitly qualified ("AND the registry has not been finalized — the ``_check_mutable()`` guard fires before the registration check, so post-finalize calls raise ``ConfigurationError`` even for unknown types"). The second paragraph ("Honours ``_check_mutable()``: after ``finalize_django_types()`` ...") is preserved intact at `registry.py:155-167`, and the new wording is consistent with it. Google convention; longest line ≤110.
- **Low 1 (anchor comment).** One short comment at `registry.py:295` directly above `if appended:` reads `# Inverse of register's mutations above; mirror any new register side-effect here on rollback.` Anchored at the rollback site (the maintenance-relevant location, not buried mid-function), names the inverse-of-register contract and the mirror obligation for future `register` side-effects. 105 columns, ≤110.

The previous logic-pass change at `registry.py:297` (formerly line 288) — `self._types[model]` bare subscript replacing the dead-defensive `self._types.get(model, [])` — is still present and unchanged by this pass.

### Scope confirmation

`git diff -- django_strawberry_framework/registry.py` shows exactly the three docstring/comment changes plus the prior logic-pass `_types[model]` simplification — nothing else. **Low 3** (`register_definition` collision phrasing) remains untouched at `registry.py:269` as the artifact mandates (forwarded to the project pass). No edits to other docstrings, no `_check_mutable` comment polish, no test changes, no `CHANGELOG.md` changes. The `conf.py` modification in the working tree is from the prior `rev-conf.md` cycle (already `verified`, awaiting maintainer commit) and is out of scope for this verification.

### Top-level Status

Unchanged — remains `fix-implemented`. Worker 2 owns that value; this sub-pass acceptance does not advance to `verified` because the changelog disposition pass has not been recorded yet.

### Verification outcome

comments accepted; awaiting changelog disposition

---

## Changelog disposition

**Warranted?** Not warranted.

**Reason.** Internal-only cycle. The one source change is a semantically equivalent simplification — the unreachable `[]` default in `self._types.get(model, [])` at `registry.py:288` was removed in favour of the bare subscript `self._types[model]`; on the rollback path `appended` is `True`, which means `register` already ran `setdefault(model, [])` and appended `type_cls`, so the default branch was unreachable. Existing rollback coverage at `tests/test_registry.py:660-878` already pins the behaviour. The other edits are docstring rewordings (`_already_registered` two-site claim, `unregister` `_check_mutable`-then-registration ordering made explicit) and one inline anchor comment above the `register_with_definition` rollback block. No public API, behavior, exception type, error message substring, or test surface change — all collision-phrasing substrings the test suite pins by `match=` (`tests/test_registry.py:70,144,203,761,775,801`) are untouched. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan `docs/review/review-0_0_6.md` (no changelog authorization for this cycle item), no `CHANGELOG.md` edit is made. The existing `[0.0.6]` entry already covers the user-visible `0.0.6` registry surface (`primary_for`, `types_for`, `models_with_multiple_types`, `unregister`, `register` return-type change, `primary` kwarg) and does not need touching for this docstring/comment cleanup.

**What was done.** No `CHANGELOG.md` edit. Disposition recorded in this artifact.

### Validation run

- `uv run ruff format .` — pass / no-changes (no source change this pass; only artifact edits).
- `uv run ruff check --fix .` — pass / no-changes.
- No `pytest` run per `START.md` standing rule.

Status: verified

---

## Verification (Worker 3, pass 3)

### Changelog verification outcome

Not warranted; `CHANGELOG.md` untouched; rationale correctly cites `AGENTS.md` and the active plan; ruff clean. The internal-only framing matches the cycle's actual diff scope.

Confirmed by inspection:

- `git diff -- CHANGELOG.md` is empty — no edit was made, matching the recorded disposition.
- The artifact's `## Changelog disposition` section records "Not warranted" with the required rationale: (a) semantically equivalent code change (`self._types.get(model, [])` → `self._types[model]` on a path where `appended=True` guarantees presence), (b) docstring/comment edits only otherwise, (c) the `AGENTS.md` rule "Do not update CHANGELOG.md unless explicitly instructed.", and (d) the active plan `docs/review/review-0_0_6.md` not authorizing a changelog pass for this cycle item. Both the `AGENTS.md` ban AND the lack of plan authorization are named — the carry-forward calibration from the conf.py cycle holds.
- "What was done" is recorded: no `CHANGELOG.md` edit; disposition captured in this artifact.
- Validation: `uv run ruff format .` and `uv run ruff check --fix .` both pass (100 files unchanged, all checks passed; standing `COM812` + formatter co-existence warning is expected).
- `git diff -- django_strawberry_framework/registry.py` matches the cycle scope exactly — the `_already_registered` docstring rewrite (lines 66-77), the `unregister` docstring update (lines 140-167), the rollback anchor comment plus bare-subscript simplification (lines 295-297). Nothing else.
- `git diff -- tests/` is empty — no test changes this cycle.

Accepted.

### Verification outcome

cycle accepted; verified
