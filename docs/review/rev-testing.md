# Review: `django_strawberry_framework/testing/` (folder pass)

Status: verified

Supersedes the on-disk `0.0.7`-era folder artifact (`Status: verified`), which predated `relay.py` and enumerated the folder as only `_wrap.py` + `__init__.py` (and referenced `review-0_0_7.md`). The active plan box (`review-0_0_9.md:108`) is unchecked. Replaced wholesale — not appended.

Scope: the `testing/` consumer-facing test-utility namespace. Two source siblings — `_wrap.py` (cooperative connection-method wrapping, Trac #37064 wrap-time half) and `relay.py` (public Relay test helpers `global_id_for` / `decode_global_id`) — plus the `__init__.py` export surface. Both per-file artifacts are closed `verified` (`rev-testing___wrap.md`, `rev-testing__relay.md`); this pass looks only for cross-file folder-scope concerns: export surface, one-way import direction, naming/docstring consistency, repeated literals.

## DRY analysis

- **Cross-file repeated literals: NONE at folder scope.** Per-file shadow overviews: `_wrap.py` = 0 repeated literals; `relay.py` = `4x global_id_for:` (intra-file message provenance, already adjudicated correctly-inline at `rev-testing__relay.md` `### DRY recap` — folding into an f-string-prefix constant would hurt readability for no behavioral gain); `__init__.py` = 0. No literal appears in two+ files, so there is no folder-level string-literal consolidation candidate. The two modules share zero string constants — they share *symbol* imports (`_is_database_failure`, `encode_typename`, the gate-message constants), which are already single-sourced.
- **`_is_database_failure` single-sourcing — defer-with-trigger carries forward verbatim.** The only cross-module shared-predicate consolidation point in the folder is `_wrap.py`'s consumption of `_django_patches.py::_is_database_failure` (`testing/_wrap.py:27` import, `:144` call), the wrap-time mirror of the unwrap-time `_django_patches.py:173` call. Single-sourced today; the import-from-`_django_patches` direction is correct because the patch module ships first at `AppConfig.ready`. Defer until a SECOND `testing/`-package consumer of `_is_database_failure` lands (e.g. a `safe_unwrap_connection_method` companion or a `GraphQLTestCase` fixture); at that point evaluate hoisting the predicate into a neutral `testing/_database_failure.py` with `_django_patches.py` re-importing it. Trigger: a second `testing/`-package call site for `_is_database_failure`. (Carried forward from `rev-testing___wrap.md` `## DRY analysis`; nothing in `relay.py` re-opens it.)
- **`encode_typename` live-emission parity — defer-with-trigger carries forward verbatim.** `relay.py::global_id_for` (`testing/relay.py:96`) computes the type-name slot by delegating to `types/relay.py::encode_typename` — the same function the live `resolve_typename` closure runs — rather than re-implementing strategy dispatch. The only candidate consolidation is a shared "encode the slot then base64-wrap" helper spanning the live closure and this helper, but the two have different return contracts (closure returns the bare slot, helper must return the finished GlobalID string). Defer until a third site needs the *finished* GlobalID string from a `(definition, strategy)` pair; extract `_finished_global_id(definition, strategy, type_cls, node_id)` then. (Carried forward from `rev-testing__relay.md` `## DRY analysis`.)

## High:

None.

## Medium:

None.

## Low:

### GLOSSARY `testing` subpackage roster omits the now-shipped `global_id_for` / `decode_global_id` public helpers

The GLOSSARY's `django_strawberry_framework.testing` subpackage symbol roster (`docs/GLOSSARY.md:41-43`, "Symbols available from the `django_strawberry_framework.testing` subpackage (consumer test utilities)") lists **only** `safe_wrap_connection_method`. The two Relay test helpers `global_id_for` / `decode_global_id` shipped this release (`0.0.9`, spec-032 Decision 10 consumer card) as public consumer-facing API at the documented `django_strawberry_framework.testing.relay` submodule path, and `testing/__init__.py`'s own module docstring lists them under "Currently exports" (`testing/__init__.py:16-26`). They appear **nowhere** in `docs/GLOSSARY.md` (grep for `global_id_for` / `decode_global_id` returns zero hits). The subpackage roster is therefore one bullet short of the namespace's actual public surface.

Why it matters: folder-scope documentation-completeness, single public-contract entry → Low. The per-file `rev-testing__relay.md` artifact correctly observed that the *GlobalID strategy system* is documented under `#relay-node-integration` / `#metaglobalid_strategy` (so no per-symbol GLOSSARY `## global_id_for` deep-dive entry is required, and that artifact's "no GLOSSARY entry expected" claim is correct at the per-symbol-deep-dive granularity). The gap surfaces only at the FOLDER lens: the *subpackage roster* — the one-line inventory of "what's importable from `testing`" — should enumerate the two shipped helpers (with their submodule-path caveat), because a consumer reading the roster to learn what the namespace offers will not discover them. This is the roster-vs-deep-dive distinction, not a contradiction of the per-file finding.

Recommended change: add a roster bullet under `docs/GLOSSARY.md:43`, matching the roster's existing reference-style link convention and wording register:

```docs/GLOSSARY.md:43
- [`safe_wrap_connection_method`](#safe_wrap_connection_method) — cooperative wrap helper …
- `global_id_for` / `decode_global_id` — public Relay test helpers at the `django_strawberry_framework.testing.relay` submodule path (NOT re-exported from the `testing` root, by design); mint and decode the strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits. See [Relay Node integration](#relay-node-integration).
```

Reuse the `#relay-node-integration` anchor the strategy system already lives under rather than minting new per-symbol anchors (consistent with the per-file artifact's "no per-symbol deep-dive expected" judgment). Because this is a real tracked-file (GLOSSARY) edit, the cycle routes through shape #4 (Worker 2 makes the edit), not the no-source-edit shape #5; `Status: under-review`.

### `__init__.py` "Future exports … planned for `0.0.12`" version-pin — forward-looking, no rot today

`testing/__init__.py:28-35` documents `TestClient` / `AsyncTestClient` / `GraphQLTestCase` as "Future exports (tracked in `docs/GLOSSARY.md`; planned for `0.0.12`)". GLOSSARY agrees verbatim (`docs/GLOSSARY.md:84,132` both read "planned for `0.0.12`"). At `0.0.9` this is an accurate forward-reservation, not rot. Per the worker-1 severity rubric, a version-pinned forward promise is Low while it stays a *future*-tense reservation and the named version is still ahead; it would PROMOTE to Medium only if `0.0.12` ships those surfaces while this docstring/GLOSSARY still says "planned", or if a same-version consumer promise turned false. Forward-looking; no action now. Trigger: when the `0.0.12` testing surfaces (`TestClient` / `GraphQLTestCase`) land, re-sweep both `testing/__init__.py:28-35` and `docs/GLOSSARY.md:84,132` in the same change so neither keeps the stale "planned" tense.

## What looks solid

### DRY recap

- **Existing patterns reused.** Both modules reuse package-canonical single sources rather than re-spelling them: `_wrap.py` consumes `_django_patches.py::_is_database_failure` (`testing/_wrap.py:27,144`); `relay.py` consumes `types/relay.py::encode_typename` + `decode_global_id` (`testing/relay.py:45`), `types/base.py`'s `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` / `STRING_GLOBALID_STRATEGIES` (`testing/relay.py:40-44`), and the uniform `exceptions.py::ConfigurationError` (`testing/relay.py:39`). Every cross-folder dependency is an import of a single source of truth.
- **New helpers considered.** Two folder-spanning helper candidates were evaluated and deferred-with-trigger (a `testing/_database_failure.py` predicate host; a shared finished-GlobalID-string helper) — both carried forward in `## DRY analysis` with explicit third-site triggers. No act-now folder-level extraction is warranted across the two siblings.
- **Duplication risk in the current folder.** None across files. The only repeated literal in the folder (`4x global_id_for:` inside `relay.py`) is intra-file intentional message provenance, already adjudicated at per-file scope. The two modules share no string constants and no near-copy logic — they are unrelated test-utility concerns (DB-connection wrapping vs Relay id minting) that happen to co-locate under the consumer-test namespace.

### Other positives

- **Export surface is intentional and internally consistent.** `testing/__init__.py:41-43` re-exports exactly one symbol (`safe_wrap_connection_method`) at the package root via `__all__ = ["safe_wrap_connection_method"]`. The Relay helpers are deliberately NOT re-exported from the root — `relay.py` lives behind the explicit `django_strawberry_framework.testing.relay` submodule path. Both the `__init__` docstring (`testing/__init__.py:16-26`) and the `relay.py` module docstring (`testing/relay.py:32-34`) give the SAME rationale for the split: keeping the heavyweight `types`-package imports out of the root `import django_strawberry_framework.testing` so light consumers (the Trac #37064 wrap helper) don't pay for them. `_wrap.py` carries no `types` import; `relay.py` is the only `types`-importing sibling. The cost-isolation claim is structurally true, not just asserted. `_wrap`'s leading-underscore module name correctly signals "private implementation reached via the `__init__` re-export, not a public import path" — consistent with the public `relay.py` (no underscore, its own public submodule path). `_wrap`'s public API IS intentionally private-by-module-name but public-by-re-export; `relay`'s is public-by-submodule-path — two deliberate, distinct publication mechanisms, both documented.
- **Import direction is strictly one-way (leaf, no back-edge).** Grep across `django_strawberry_framework/` (excluding `testing/` itself) returns ZERO imports FROM `testing/` — nothing in the package internals depends back on the test-utility namespace. The folder imports OUT to `_django_patches`, `exceptions`, `types/base`, `types/relay`, and the stdlib/Django/Strawberry surface; nothing imports back in. `testing/` is a pure consumer leaf of the package's public + internal surface, which is the correct shape for a consumer-facing test-utility namespace. No circular-import risk.
- **Naming / error-handling consistency across the two siblings.** Both helpers fail LOUD with package-canonical exceptions rather than returning sentinels or silently degrading: `_wrap.py` raises `TypeError` for a non-callable wrapper (and the documented-correct loud `AttributeError` on a bogus `method_name`); `relay.py` raises the uniform `ConfigurationError` across all four mint-refusal branches, each message prefixed with its own `global_id_for:` provenance. Both modules write Google-flavored docstrings with a module-level framing block plus per-symbol detail, and both cite their governing reference (Trac #37064 / spec-032 Decision 10) in-docstring. The naming register is consistent: `safe_wrap_connection_method` (verb-led action helper), `global_id_for` / `decode_global_id` (Relay `node(id:)` consumer vocabulary, `noqa: A002` on `id` deliberately mirroring Relay's parameter name).
- **Both per-file artifacts independently `verified`.** `rev-testing___wrap.md` (3 Lows, all comment-tier, act-now Low already-satisfied at baseline) and `rev-testing__relay.md` (0 findings, shape #5) both reached `Status: verified` with independent Worker 3 verification (the relay artifact's Worker 3 drove all four raise branches + live-emission parity live). No per-file finding is re-opened at folder scope.
- **`__init__.py` is a clean re-export module.** Shadow overview confirms: 1 import, 0 symbols, 0 calls of interest, 0 repeated literals, 0 control-flow. Pure docstring + single re-export + `__all__`. No executable surface to review beyond the export decision (covered above).

### Summary

The `testing/` folder is a well-factored consumer-facing test-utility namespace: two unrelated single-purpose modules (Trac #37064 connection-method wrapping; Relay GlobalID minting/decoding) co-located behind a deliberately minimal root export. Import direction is strictly one-way — `testing/` is a pure leaf with no back-edge into package internals, no circular-import risk. The export surface is intentional and consistently rationalized in both docstrings: only `safe_wrap_connection_method` is re-exported at the root (private-by-module-name, public-by-re-export), while the heavier `types`-importing Relay helpers stay behind the public `testing.relay` submodule path to keep the root import light. Naming, error-handling (loud canonical exceptions over sentinels), and docstring shape are consistent across the two siblings. No cross-file repeated literals, no folder-level helper extraction warranted (two defer-with-trigger candidates carried forward). No High, no Medium. Two Lows: one act-now folder-scope GLOSSARY roster-completeness gap (the `testing` subpackage roster omits the now-shipped `global_id_for` / `decode_global_id`; routes through shape #4 as a GLOSSARY edit → `under-review`), one forward-looking version-pin (`0.0.12` future-exports tense, no rot today, trigger recorded).

---

## Fix report (Worker 2)

Consolidated single-spawn (shape #4 GLOSSARY-prose, in-cycle edit is a single roster bullet; the second Low is forward-looking with no edit). Logic + comment + changelog disposition recorded together; bare `Status: fix-implemented`.

### Files touched
- `docs/GLOSSARY.md` (the `testing` subpackage roster, under the `safe_wrap_connection_method` bullet in the "Symbols available from the `django_strawberry_framework.testing` subpackage" block) — added a roster bullet for the now-shipped public Relay test helpers `global_id_for` / `decode_global_id`. They were importable at `django_strawberry_framework.testing.relay` since `0.0.9` (spec-032 Decision 10) but appeared nowhere in GLOSSARY (grep zero hits). Bullet added verbatim from the artifact's recommended text; verified accurate against `testing/relay.py` source (`__all__ = ["decode_global_id", "global_id_for"]`; both at the submodule path, neither re-exported from the `testing` root — the root `__init__` `__all__` is `["safe_wrap_connection_method"]` only; `global_id_for` mints / `decode_global_id` decodes the strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits). Reused the existing in-page `#relay-node-integration` anchor (verified present, referenced 13+ times in GLOSSARY) rather than minting per-symbol anchors — consistent with the per-file artifact's "no per-symbol deep-dive expected" judgment. No new per-symbol GLOSSARY entry, no Index/See-also row touched (roster-completeness only, the helpers intentionally have no own entry).

### Tests added or updated
- None. Doc-only GLOSSARY roster edit; no source/behaviour change, nothing to pin. The helper names/behavior were confirmed against `testing/relay.py` (not via test execution).

### Validation run
- `uv run ruff format .` — pass (no changes; 265 files left unchanged)
- `uv run ruff check --fix .` — pass (all checks passed)
- `uv.lock` — clean (no modification; nothing to restore)

### Notes for Worker 3
- No shadow file used (doc-only roster edit; the artifact's recommended text was lifted, then cross-checked against `testing/relay.py` lines 1-47/50-97).
- Premise re-verified in source before editing: `testing/relay.py` `__all__ = ["decode_global_id", "global_id_for"]`; `testing/__init__.py` re-exports only `safe_wrap_connection_method`; `grep -n "global_id_for\|decode_global_id" docs/GLOSSARY.md` returned zero hits at baseline. The `#relay-node-integration` anchor exists. No false-premise rejection.
- No inline cross-file `](path)` link introduced. The new bullet uses only an in-page anchor (`](#relay-node-integration)`), matching the roster's existing inline-anchor convention (the `safe_wrap_connection_method` bullet uses the same style). No LINK-DEFINITIONS block change needed.
- `git diff <baseline> -- docs/GLOSSARY.md` already carried prior-cycle GLOSSARY edits (DjangoConnection, Meta.orderset_class, OrderSet, RelatedFilter, RelatedOrder, inspect_django_type); my one-bullet add stacks on top — `git diff --stat` vs baseline shows GLOSSARY.md only.
- Low 2 (the `0.0.12` TestClient/GraphQLTestCase future-export version-pin) left untouched per dispatch — forward-looking, no rot at `0.0.9`; trigger recorded in the artifact.

---

## Verification (Worker 3)

### Logic verification outcome
- **Low 1 (roster bullet) — accepted as accurate.** The added bullet (`docs/GLOSSARY.md`, under the `safe_wrap_connection_method` bullet in the `testing` subpackage roster block) is the sole GLOSSARY hunk this cycle owns; the `git diff <baseline> -- docs/GLOSSARY.md` `+` line matches the artifact's recommended text verbatim. Every factual claim confirmed at source: `global_id_for` / `decode_global_id` live at `django_strawberry_framework.testing.relay` and are in `relay.py` `__all__ = ["decode_global_id", "global_id_for"]`; they are NOT re-exported from the `testing` root — `testing/__init__.py` `__all__ = ["safe_wrap_connection_method"]` only; the `#relay-node-integration` in-page anchor resolves (`## Relay Node integration` heading at `docs/GLOSSARY.md` line 1051). No cross-file `](path)` link introduced — bullet uses only the in-page `](#relay-node-integration)` anchor, matching the sibling `safe_wrap_connection_method` bullet's convention; no LINK-block change needed.
- **Low 2 (`0.0.12` future-export version-pin) — confirmed left forward-looking.** No edit to `testing/__init__.py:28-35` or the GLOSSARY `planned for 0.0.12` lines; accurate forward-reservation at `0.0.9`, trigger recorded. The owned GLOSSARY change is the roster bullet only.
- **Folder-pass conclusions sanity-checked, all hold.** Import direction strictly one-way (`testing/` is a pure consumer leaf, no back-edge); export surface intentional (root re-exports only `safe_wrap_connection_method`, Relay helpers behind the `testing.relay` submodule path to keep the root import light); naming / error-handling / docstring consistency across `_wrap.py` and `relay.py` — all consistent with my own prior per-file acceptances of both siblings (`rev-testing___wrap.md`, `rev-testing__relay.md`, both verified). No real folder-level defect missed.
- **Shape #5 / no-source-edit posture confirmed.** `git diff --stat <baseline> -- django_strawberry_framework/testing/` is EMPTY (byte-unchanged) — the folder pass authored zero source edits; the only owned change is the GLOSSARY prose bullet (shape #4, correctly routed by Worker 2 as a tracked-GLOSSARY edit, not shape #5).

### DRY findings disposition
- Both folder-level candidates carried forward as defer-with-trigger, unchanged: (1) `_is_database_failure` single-sourcing — trigger = a second `testing/`-package consumer; (2) `encode_typename` finished-GlobalID-string extraction — trigger = a third site needing the finished GlobalID from a `(definition, strategy)` pair. The intra-file `4x global_id_for:` provenance literal correctly stays inline (adjudicated at per-file scope). No act-now folder-level extraction warranted.

### Temp test verification
- None used. Doc-only GLOSSARY roster edit, no source/behaviour change to pin; bullet facts confirmed by `git grep` of `__all__` in `relay.py` / `__init__.py` and the anchor-heading grep.

### Sibling-cycle attribution
- The other GLOSSARY hunks in the baseline diff (DjangoConnection ~287, Meta.orderset_class ~804, OrderSet ~916, RelatedFilter ~992, RelatedOrder ~1002, inspect_django_type ~1179) and the dirty source paths (conf / connection / exceptions / filters.factories / filters.sets / list_field / inspect_django_type / optimizer.extension / selections / walker / orders.factories / orders.inputs + 2 tests) all attribute to CLOSED sibling cycles I have independently verified+[x] in prior passes this release. Not a rejection trigger; the folder pass's "Files touched: docs/GLOSSARY.md only (one bullet)" holds — `testing/` source is byte-unchanged.

### Verification outcome
- `cycle accepted; verified`

---

## Comment/docstring pass

Consolidated into the single spawn (the in-cycle edit IS prose; there is no separate source comment/docstring surface to revisit).

### Files touched
- None beyond the `docs/GLOSSARY.md` roster bullet recorded in the Fix report. No source comment or docstring was changed (no source edit this cycle).

### Per-finding dispositions
- Low 1 (GLOSSARY `testing` subpackage roster omits `global_id_for` / `decode_global_id`): fixed — roster bullet added, reusing the in-page `#relay-node-integration` anchor; verified against `testing/relay.py` source.
- Low 2 (`__init__.py` / GLOSSARY `0.0.12` future-export version-pin): forward-looking, no action. Accurate forward-reservation at `0.0.9`; trigger recorded in the artifact (re-sweep `testing/__init__.py:28-35` + `docs/GLOSSARY.md` "planned for `0.0.12`" lines when the `0.0.12` testing surfaces land).

### Validation run
- `uv run ruff format .` — pass (no changes; 265 files unchanged)
- `uv run ruff check --fix .` — pass (all checks passed)

### Notes for Worker 3
The bullet uses an in-page anchor only; no cross-file `](path)` link, no LINK-DEFINITIONS block change.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Doc-only GLOSSARY roster-completeness edit (one bullet enumerating already-shipped public helpers). No source, no behaviour change, no new consumer-visible surface — `global_id_for` / `decode_global_id` already shipped in `0.0.9` (spec-032 Decision 10); this only documents them. Cite BOTH: `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly instructed"), AND the active plan's silence on changelog authorization for this cycle — the dispatch prompt explicitly says "Do NOT edit CHANGELOG.md" and authorizes only `docs/GLOSSARY.md`. Additionally, per the standing pattern, a per-file/folder cycle is NEVER the authorising scope for a CHANGELOG edit; any drift forwards to the project pass.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (no changes)
- `uv run ruff check --fix .` — pass

---

## Iteration log

(none)
