# Review: `django_strawberry_framework/filters/factories.py`

Status: verified

## DRY analysis

- **Top-level unordered-key sorting vs. `_make_hashable`'s sorting differ (`key=repr` only in the helper).** `_make_cache_key`'s dict-`fields` branch (`factories.py::_make_cache_key #"sorted((k, _make_hashable(v)) for k, v in fields.items())"`, src 149-153) and its extra-meta branch (src 161-165) call bare `sorted(...)` (natural tuple ordering), while `_make_hashable`'s dict / set branches (src 118-123) sort by `key=repr`. The two paths are correct as written (top-level keys are always `str` field/meta names so natural sort cannot raise; the helper's `key=repr` defends the nested mixed-type case), but the two sort strategies are a near-duplicate "canonicalize an unordered container" operation expressed two ways. Defer until a third call site needs canonical unordered-container ordering; then extract a single `_sorted_pairs(items)` helper that always sorts `key=repr` and route all three (the two `_make_cache_key` branches + `_make_hashable`'s dict branch) through it, so the mixed-key-type defense is uniform rather than living only in the helper. Not act-now: forcing `key=repr` into the top-level branches today buys nothing (keys are strings) and the extraction adds a helper for a 2-line body.
- **Layer-6 dynamic-cache half is the filter-side twin of the (not-yet-shipped) order side.** `orders/factories.py` carries a comment naming the parallel `_dynamic_filterset_cache` analogy (`orders/factories.py #"_dynamic_filterset_cache"`, src ~88-89) and ships only the BFS layer today. The neutral BFS substrate is already single-sited in `utils/inputs.py::GeneratedInputArgumentsFactory`; the Layer-6 dynamic-cache half (`_make_hashable` / `_make_cache_key` / `_create_dynamic_filterset_class` / `get_filterset_class` / `_RESERVED_FACTORY_KEYS`) is NOT yet shared. Defer until the order side ships its own dynamic cache and carries a working `get_orderset_class`; then lift `_make_hashable` + `_make_cache_key` + the reserved-key strip + the cache get/build/store skeleton into `utils/inputs.py` as `make_generated_set_cache_key(safe_meta)` + `get_or_build_dynamic_set(cache, reserved_keys, factory, safe_meta)`, leaving only the family-specific `_create_dynamic_*_class` and the per-family module-global cache dict at each call site. Trigger: the order-side dynamic-cache half lands.

## High:

None.

## Medium:

### Forward-looking entry point is unconsumed by any source path at 0.0.9 — verify the wiring landed or correct the docstring

The module docstring (src 6-8) and `get_filterset_class`'s docstring (`factories.py::get_filterset_class #"the connection-field surface owning this entry point lands in"`, src 196-197) both assert the Layer-6 dynamic-cache surface is for connection fields and that the owning surface "lands in `0.0.9`". At 0.0.9 the connection field exists (`connection.py`) but consumes the **already-resolved** `definition.filterset_class` sidecar directly (`connection.py #"definition.filterset_class.apply_sync"`, src 860-861 / 885-886) and never calls `get_filterset_class`, never touches `_dynamic_filterset_cache`, and never builds a dynamic FilterSet. A repo-wide grep confirms `get_filterset_class` has zero call sites outside this file and its tests; the entire Layer-6 half (`get_filterset_class`, `_create_dynamic_filterset_class`, `_make_cache_key`, `_make_hashable`, `_dynamic_filterset_cache`, `_RESERVED_FACTORY_KEYS`) is built-and-tested but **dead from any non-test source path**.

Why it matters: this is a contract-accuracy issue, not a correctness bug — the cache logic itself is sound (see "What looks solid"). But the docstring promises a 0.0.9 connection-field consumer that does not exist, so a maintainer reading the file at 0.0.9 will hunt for a wiring seam that was never cut. Two legitimate root causes, and the correct fix depends on which is true (this is the load-bearing reason this is Medium-with-verification rather than a Low comment tweak):

1. The connection-field-without-explicit-`filterset_class` surface was deferred past 0.0.9. Then both docstrings should name the actual deferral target (a spec card / version), not a shipped "lands in `0.0.9`" claim that is now self-falsifying, and the comment block (src 30-43) keeps its "this cache has NO clear hook ... add one if a consumer reload path ever demands it" caveat framed as still-hypothetical.

2. The surface was meant to land in 0.0.9 and the wiring is genuinely missing. Then this is a real gap: a connection field targeting a model without an explicit `filterset_class` has no path to the dynamic cache, and the advertised "two connection fields targeting the same model resolve to the same generated class" break-glass is unreachable.

Recommended: confirm against the active spec which case holds. If (1), rewrite both docstrings to a version-agnostic form (e.g. "consumed by the connection-field auto-filterset surface; deferred, see spec-NNN") — same drift class as the version-pinned-docstring rot flagged in worker-1 memory for `exceptions.py::OptimizerError`. If (2), the connection field needs a follow-up to route its no-explicit-filterset case through `get_filterset_class` — that is a connection.py/finalizer concern, not a local edit here, so forward it to the folder pass (`rev-filters.md`) and project pass (`rev-django_strawberry_framework.md`) rather than treating it as a defect in this file. No test change is required for case (1); the existing `tests/filters/test_factories.py` Layer-6 coverage already pins the cache contract.

## Low:

### `_create_dynamic_filterset_class` shallow-copies `safe_meta`, leaving `Meta.fields` aliased to the caller's live container

`meta_attrs = dict(safe_meta)` (`factories.py::_create_dynamic_filterset_class #"meta_attrs = dict(safe_meta)"`, src 184) is a shallow copy: a list/dict-shaped `fields` (or `exclude`) value remains the caller's object, attached verbatim onto the synthesized `Meta` class. The cache **key** is already frozen at call time (`_make_hashable` produces fresh tuples), so a later mutation of the caller's list cannot corrupt a future cache lookup — the key/value divergence is the only hazard, and django-filter reads `Meta.fields` once at filterset-class-creation (`type(name, (FilterSet,), {"Meta": meta_class})`, src 187) so the aliased container is consumed before any realistic re-mutation window. This is why it is Low, not Medium: there is no request-scope or cross-request state at stake (the cache is process-global build-time infrastructure; the generated class is immutable once built). Defer with trigger: if a future caller ever mutates a `Meta.fields` list after passing it to `get_filterset_class` (e.g. an incremental field-registration path), deep-copy the mutable meta values here. Until then the shallow copy is the correct cost.

### Module docstring "the finalizer materializes the built classes as module globals" describes only the BFS half

The closing module-docstring sentence (src 13-15) attributes module-global materialization to the finalizer for "the built classes". This is accurate for the Layer-5 BFS factory output (`finalizer.py` runs `FilterArgumentsFactory(...).arguments` and materializes via `utils/inputs.py::materialize_generated_input_class`) but does not apply to the Layer-6 dynamic FilterSet *classes* — those are plain `type(...)` products cached in `_dynamic_filterset_cache`, never materialized as module globals (only their downstream generated *input* classes would be, once a consumer exists). The sentence reads as if it covers both halves of the module. Minor clarity only; reword to scope it to the BFS factory's input classes. Fold into the same docstring edit if the Medium resolves to case (1).

## What looks solid

### DRY recap

- **Existing patterns reused.** The BFS walk, per-class collision check (`_type_filterset_registry`), idempotent `input_object_types` cache, and subclass-rejection guard all live once in `utils/inputs.py::GeneratedInputArgumentsFactory` (src 277-417); `FilterArgumentsFactory` (src 52-97) supplies only the six family-hook class attrs + the `_build_input_triples` override that appends `_build_logic_fields` (the `and_`/`or_`/`not_` bag, src 90-97). This is the realized 0.0.9 DRY consolidation (`docs/feedback.md` Major 1) — the neutral machinery is not re-spelled here. NOTE: the stale 0.0.7 artifact's two Lows (a pure-passthrough triples comprehension in `_build_class_type`; the `_make_hashable` dict-branch mixed-key `TypeError`) are BOTH already merged in current source — the comprehension is gone (`_build_input_triples` returns the splat directly, src 97) and the dict branch now sorts `key=repr` (src 121, pinned by `test_make_hashable_dict_branch_supports_mixed_key_types`). Did NOT re-raise.
- **New helpers considered.** A shared `_sorted_pairs(key=repr)` for the three unordered-container sort sites was evaluated and deferred (DRY analysis bullet 1) — the top-level branches are provably safe with natural sort, so extraction is net-negative today. The cross-family Layer-6 cache extraction was evaluated and deferred to the order-side dynamic-cache landing (DRY analysis bullet 2).
- **Duplication risk in the current file.** The 2x `"filterset"` literal flagged by the static helper is the `_rename_noun` / `_related_target_attr` family-hook pair (src 87-88); they are distinct knobs that happen to share a token, not a duplicated constant — correct as-is.

### Other positives

- **Cache-key canonicalization is correct and well-bounded.** `_make_hashable` (src 105-126) sorts unordered containers (`dict`, `set`, `frozenset`) by `key=repr` so mutually-unorderable mixed member/key types (`{1,"a"}`, `{"a":1,0:2}`) never trip Python's default `<` comparison — pinned by `tests/filters/test_factories.py:328`. Ordered containers (`list`/`tuple`) preserve order because list-shaped `Meta.fields` defines filter order. The `set`-shaped-`fields` iteration-order caveat is honestly documented (src 140-145) and produces cache *misses*, never wrong *hits* — a conservative failure mode.
- **Cache keys embed model identity, so `registry.clear()` can never produce a wrong hit.** The no-clear-hook lifecycle (src 37-43) is sound: a rebuilt model class is a new identity, so `(model, ...)` keys naturally partition pre- and post-clear builds; a stale entry is parked, never returned for a fresh model. The comment correctly frames this as a test-isolation nicety with no real-world cost. (Mirrors the model-keyed-vs-type-keyed reasoning in worker-1 memory's registry.py entry.)
- **No request-scope or mutable-shared state.** The cache value is an immutable generated class; the key tuple is fully hashable/immutable; `get_filterset_class` returns an explicit class unchanged (src 216-217) before any keying, and the reserved-key strip (src 218) runs on a fresh dict comprehension. No per-request data is keyed or stored — process-global build-time only.
- **BFS termination is guaranteed.** The walk's `seen` set + enqueue-time `target not in seen` gate (`utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`, src 368-394) makes cycles (`A->B->A`, self-referential filters) terminate; `RelatedFilter(None,...)` placeholders are skipped via the `target is not None` guard (src 393). FIFO `pending.pop(0)` gives deterministic build order. Pinned by `test_factories.py` self-referential + cyclic cases (src 73-91).
- **`ConfigurationError` on missing `model`** (src 180-183) is the right exception type (consistent with the package's deferred-key / misuse vocabulary) and names the actionable fix; pinned by `test_get_filterset_class_requires_model_when_dynamic`.
- **Subclassing rejection** is enforced at class-creation in the shared base's `__init_subclass__` (`utils/inputs.py` src 324-338) and tested here (`test_factories.py:501`), preventing the shared-mutable-cache cross-contamination the class docstring warns about (src 75-78).

### Summary

A small, well-factored build-only module: the BFS half is a thin family specialization over the single-sited `GeneratedInputArgumentsFactory`, and the Layer-6 dynamic-cache half is logically sound — correct hashable-key canonicalization, conservative miss-not-wrong-hit failure modes, no request-scope or mutable-shared state, and model-identity keys that make the no-clear-hook lifecycle safe. BFS termination and collision detection are guaranteed by the shared base. The one substantive finding is contract-accuracy, not correctness: the Layer-6 entry point (`get_filterset_class` and its dynamic cache) is built-and-tested but has zero source consumers at 0.0.9, while two docstrings assert the owning connection-field surface "lands in `0.0.9`". That needs a spec check to decide between rewording the now-self-falsifying version claim (case 1, local docstring edit) or forwarding a genuine wiring gap to the folder/project pass (case 2). Two Lows (shallow-copy aliasing deferred-with-trigger; module-docstring scope) and two deferred DRY opportunities round it out. No High; no request-state, mutability, or ORM-correctness risk in the cache.

---

## Fix report (Worker 2)

Consolidated single-spawn (qualifying shape: the only in-cycle edits are docstring/comment rewords with no logic change and no test change; the Medium resolved to case (1) deferred, a local docstring edit). Logic + comment + changelog dispositions collapsed into one pass.

### Spec-fact investigation (the Medium's load-bearing verify)

The Medium hinges on case (1) deferred vs case (2) missing-wiring. Confirmed **case (1) — DEFERRED**, not a wiring gap. Evidence:

- **Grep for `get_filterset_class` callers (source AND tests):** zero non-test source callers. Only sites: the definition + a string in the `ConfigurationError` message + a comment ref (`factories.py:47/181/190/194`), the test file (`tests/filters/test_factories.py` — 18 hits, all import/call of the symbol under test), and a comment in `orders/factories.py #"mirrors ``filters/factories.py::get_filterset_class``"` (the parallel-reserve note, not a call). No source path calls it.
- **The shipped 0.0.9 connection field does NOT consume it.** `spec-030-connection_field-0_0_9.md` (DjangoConnectionField, status `shipped (0.0.9)` per its Status line + KANBAN `DONE-030-0.0.9`) reads the wrapped type's **already-resolved** `Meta.filterset_class` sidecar directly: spec-030 lines 37 ("the connection field's `filter:` argument is auto-derived from … reuses the `apply_sync` / `apply_async` … `filter_input_type`"), 244, 397; source at `connection.py #"definition.filterset_class.apply_sync"` (src 860-861 / 885-886) and the resolver-signature builder `connection.py #"filter_input_type(definition.filterset_class)"` (src 930-931). spec-030 requires an **explicitly declared** `filterset_class` on the type; it never auto-derives a FilterSet from `model` / `fields` and never routes through `get_filterset_class`.
- **The auto-FilterSet-from-model surface is a standing deferred Non-goal.** `spec-027-filters-0_0_8.md` Non-goals #"Auto-generation of ``FilterSet`` from ``Meta.fields``": *"Deferred; the dynamic-factory machinery (Layer 6) exists for the connection-field path … Direct consumer-facing implicit generation lands when `DjangoConnectionField` ships in `0.0.9`."* And Layer 6 #"the connection-field consumer is `0.0.9`" (src 550): *"This card lands the cache plumbing; the connection-field consumer is `0.0.9`."* That prediction was **not realized** — spec-030 shipped an explicit-sidecar-only design, so the auto-derive consumer the cache was built for was never cut. No later spec owns it: grep of spec-032 / spec-033 / spec-034 / BACKLOG.md for `auto.?filterset` / `get_filterset_class` / `implicit.*filterset` / `layer.?6` returned nothing. So the consumer is genuinely deferred past 0.0.9 with no current owning card beyond spec-027's deferred Non-goal — and the docstring "lands in `0.0.9`" is self-falsifying drift (same class as the version-pinned-docstring rot in worker-1 memory for `exceptions.py::OptimizerError`).

Because this is case (1), there is **no wiring gap to forward** to the project pass — the absence of a consumer is the documented, intended deferred state, not a missing seam that should exist at 0.0.9. The cache logic itself is sound (per "What looks solid"); only the docstrings overpromised a 0.0.9 consumer.

### Files touched

- `factories.py` module docstring (src 1-15→1-25) — retitled to name the cache "(currently unconsumed)"; reworded the Layer-6 purpose from "connection fields that target the same model without an explicit `filterset_class`" to "an auto-FilterSet surface that would let a field target a model without an explicit `filterset_class`"; added a paragraph stating Layer 6 has no source consumer, that spec-030's connection field reads the resolved sidecar directly, that auto-generation is a deferred `spec-027` Non-goal, and that Layer 6 stays build-and-test-only until that surface ships. (Resolves Medium case (1).)
- `factories.py` module docstring closing sentence (Low 2) — scoped "the finalizer materializes the built classes as module globals" to "the **BFS factory's built input classes**", and appended a parenthetical noting Layer 6's dynamic FilterSet classes are plain `type(...)` products cached below, never materialized as module globals.
- `factories.py::get_filterset_class` docstring (src ~196-197) — replaced the self-falsifying "the connection-field surface owning this entry point lands in `0.0.9`" with the accurate deferred state: no source consumer yet; the auto-FilterSet surface that would call it is a deferred `spec-027` Non-goal; spec-030's `DjangoConnectionField` consumes the resolved `Meta.filterset_class` sidecar directly and does not route through here; built-and-tested ahead of that consumer. (Resolves Medium case (1).)
- `factories.py` `_dynamic_filterset_cache` lead comment (src 30-35) — reframed the duplicate-`__name__` break-glass from a live "two connection fields … resolve to the same generated class" claim to the deferred/unconsumed auto-FilterSet framing ("No source path exercises this yet … build-and-test-only at `0.0.9`"). The lifecycle caveat (no-clear-hook, model-identity-keyed, "add a clear hook only if a consumer reload path ever demands it", src 37-43) is **preserved verbatim** and stays correctly framed as still-hypothetical, per the Medium case (1) instruction.

Low 1 (shallow-copy `dict(safe_meta)` aliasing `Meta.fields`): **no edit** — Worker 1 flagged it defer-with-trigger ("if a future caller ever mutates a `Meta.fields` list after passing it to `get_filterset_class`, deep-copy"). Trigger has not fired; shallow copy is the correct cost today (the cache key is frozen at call time via `_make_hashable`, and django-filter reads `Meta.fields` once at class creation). Preserved forward-looking.

DRY bullets 1 and 2: both forward-looking (defer-with-trigger) per Worker 1's prose — `_sorted_pairs(key=repr)` extraction deferred until a 3rd canonical-unordered-container site; cross-family Layer-6 cache lift into `utils/inputs.py` deferred until the order-side dynamic cache + working `get_orderset_class` lands. No edit.

### Tests added or updated

None. The Medium resolved to case (1) (docstring-only); Worker 1 stated no test change is required and the existing `tests/filters/test_factories.py` Layer-6 coverage already pins the cache contract (`test_get_filterset_class_*`, `test_make_hashable_dict_branch_supports_mixed_key_types`, the self-referential/cyclic cases). No behaviour changed. AGENTS.md forbids running pytest; not run.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files left unchanged; only the standing COM812-vs-formatter advisory warning).
- `uv run ruff check --fix .` — pass (all checks passed).
- No focused tests (docstring/comment-only; no executable lines changed).
- `git diff --stat` vs baseline `0872a20f`: `factories.py | 41 ++++-- ` → 31 insertions, 10 deletions. File was unchanged-since-baseline, so the cycle diff is solely these docstring/comment blocks. `uv.lock` untouched.

### Notes for Worker 3

- **Shadow file used:** `docs/shadow/django_strawberry_framework__filters__factories.overview.md` (read-only review aid; consulted for symbol/line map, not edited). Shadow line numbers are non-canonical — source line numbers cited above.
- **Spec-fact verdict:** case (1) DEFERRED. Re-verifiable via: grep `get_filterset_class` (zero non-test source callers), `spec-027` Non-goals #"Auto-generation of ``FilterSet`` from ``Meta.fields``" (deferred), `spec-030` lines 37/244/397 + `connection.py #"definition.filterset_class.apply_sync"` (explicit-sidecar-only consumer). No wiring-gap Medium forwarded to `rev-django_strawberry_framework.md` — case (2) was disproven, so there is no missing seam to forward.
- **Lifecycle caveat preserved verbatim** (src 37-43) — confirm it reads unchanged and still hypothetical.
- No false-premise rejection: Worker 1's Medium premise (zero source consumers; docstrings overpromise) held exactly; only the case-(1)-vs-(2) branch needed the spec check, which selected (1).

---

## Verification (Worker 3)

Terminal-verify on a bare `Status: fix-implemented` (consolidated single-spawn: docstring/comment-only, no logic/test change). Diff confirmed docstring/comment-only against baseline `0872a20f` (`factories.py | 41 +-`, 31 ins / 10 del; every changed line is inside a module docstring, the `_dynamic_filterset_cache` lead comment, or `get_filterset_class`'s docstring — no executable line touched). Independently re-derived the Medium spec-fact and sanity-checked the cache logic rather than trusting the artifact.

### Logic verification outcome

**Medium (forward-looking entry point unconsumed — case (1) DEFERRED) — confirmed independently.**
- **Independent grep for `get_filterset_class` source callers: ZERO.** `grep -rn "get_filterset_class" --include="*.py"` (excl. `.venv`) returns only: the definition + the `ConfigurationError` message string + the `_RESERVED_FACTORY_KEYS` comment in `factories.py` (62/196/205/209), 18 hits in `tests/filters/test_factories.py` (all import/call of the symbol under test), and one comment ref in `orders/factories.py:88` (`mirrors ``filters/factories.py::get_filterset_class```, not a call). No non-test source path calls it.
- **connection.py does NOT route through it.** `grep` for `get_filterset_class` / `_dynamic_filterset_cache` / `_create_dynamic_filterset` in `connection.py`: NONE. The field consumes the already-resolved sidecar directly — `definition.filterset_class.apply_sync` (`connection.py:860-861`), `apply_async` (`:885-886`), and `filter_input_type(definition.filterset_class)` for the signature (`:930-931`). Matches the artifact's cited lines exactly.
- **The deferral is documented, not a wiring gap.** `docs/SPECS/spec-027-filters-0_0_8.md:203` Non-goal: "Auto-generation of `FilterSet` from `Meta.fields` without declaring an explicit class. **Deferred**…"; `:550` Layer 6: "(This card lands the cache plumbing; the connection-field consumer is `0.0.9`.)" — a prediction that was NOT realized. `docs/SPECS/spec-030-connection_field-0_0_9.md` (`DONE-030-0.0.9` per KANBAN:64/103) reads the wrapped type's pre-declared `Meta.filterset_class` at construction time (`:37/:244/:397`) and never auto-derives a FilterSet from `model`/`fields`. No later spec owns the consumer: grep of `spec-03*` / `BACKLOG.md` for `get_filterset_class` / `auto.?filterset` / `implicit.*filterset` returned nothing. Case (1) holds; case (2) (missing wiring) is disproven, so nothing forwarded to the project pass.
- **Docstrings now accurate.** The new module docstring (src 1-18), `get_filterset_class` docstring (src 209-218), and the cache lead comment (src 43-50) describe the surface as build-and-test-only / unconsumed-deferred, cite the `spec-027` Non-goal and spec-030's direct-sidecar consumer, and no longer claim "lands in `0.0.9`" (the self-falsifying version pin is gone, confirmed absent in the diff — the only remaining `0.0.9` tokens scope the cache as "build-and-test-only at `0.0.9`", which is accurate).

**Low 1 (shallow-copy `dict(safe_meta)` aliasing) — correctly deferred-forward, no edit.** Trigger (a caller mutating `Meta.fields` post-call) has not fired; cache key is frozen at call time and django-filter reads `Meta.fields` once at `type(...)` creation. Forward-looking framing preserved.

**Low 2 (module-docstring scope) — addressed.** The finalizer-materialization sentence is now scoped to "the BFS factory's built input classes" with a parenthetical noting Layer 6's dynamic FilterSet classes are plain `type(...)` products, never module globals (diff src 22-27). Accurate.

**Cache-logic sanity (Worker 1's "looks solid", independently re-checked):** no correctness defect found.
- Model-identity keys: a no-DB probe (`docs/review/temp-tests/filters_factories/probe.py`) confirmed two distinct model objects produce distinct keys and the model is the primary discriminator by identity (`key[0] is model`) — so `registry.clear()` rebuilds (new model identity) can never produce a wrong hit, exactly as the preserved lifecycle caveat claims.
- `_make_hashable` mixed-type `{1,"a"}` / `{"a":1,0:2}` canonicalize order-independently without raising (`key=repr` total order); list order preserved; distinct lookups → distinct keys; keys hashable as dict keys.
- No request-scope state: cache value is an immutable generated class; key is a hashable tuple; reserved-key strip runs on a fresh dict comprehension. Process-global build-time only.
- BFS termination: the `seen`-set enqueue gate lives in `utils/inputs.py::GeneratedInputArgumentsFactory` (unchanged from baseline, outside this diff), exercised by the existing self-referential/cyclic tests. No regression possible from a docstring-only diff.
- **Lifecycle caveat preserved verbatim**: `git show <baseline>:…factories.py` vs current — the "NO clear hook / test-isolation nicety / keys embed the model identity / Add a clear hook only if…" block is byte-identical (only line numbers shifted by the docstring text added above it).

### DRY findings disposition

Both DRY bullets carried forward (defer-with-trigger), no edit — consistent with Worker 1's prose: (1) `_sorted_pairs(key=repr)` extraction deferred until a 3rd canonical-unordered-container site (top-level branches provably safe with natural sort since keys are `str`); (2) cross-family Layer-6 cache lift into `utils/inputs.py` deferred until the order-side dynamic cache + working `get_orderset_class` lands.

### Sibling-cycle attribution

Working-tree dirty paths NOT owned by this cycle (factories.py is the only owned path, and its diff is docstring-only):
- `docs/GLOSSARY.md` (1 line, the `DjangoConnection` entry) attributes to closed sibling cycle `rev-connection.md` (`Status: verified`, `[x]` at review-0_0_9.md:71) — the working-tree hunk is byte-identical to that artifact's verbatim replacement text. Not a rejection trigger.
- `conf.py` / `exceptions.py` / `list_field.py` source hunks attribute to closed sibling cycles `rev-conf.md` / `rev-exceptions.md` / `rev-list_field.md` (all `Status: verified`, `[x]` at review-0_0_9.md:70/72/73).
- Deleted root `feedback2.md` / `feedback3.md` = AGENTS.md #33 concurrent-maintainer work; untouched.
- `factories.py`'s own "Files touched" claim (docstring/comment blocks only) holds: the `git diff --stat` shows `factories.py` as the sole owned-path change and it is wholly inside docstring/comment regions.

### Temp test verification

- `docs/review/temp-tests/filters_factories/probe.py` — no-DB probe of `_make_hashable` / `_make_cache_key` (model-identity partitioning, mixed-type canonicalization, list-order preservation, key hashability). All assertions passed.
- Disposition: deleted (no behavior bug found; the cache contract is already pinned by `tests/filters/test_factories.py`). Not promoted.

### Changelog disposition

`Not warranted`. `git diff -- CHANGELOG.md` empty (confirmed). Disposition cites BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle. Internal-only framing is honest: the cycle is docstring/comment-only and the affected surface has zero source consumers, so no public-API behavior changed — "Not warranted" (not "deferred to maintainer") is the correct state.

### Validation

- `uv run ruff format --check django_strawberry_framework/filters/factories.py` — "1 file already formatted".
- `uv run ruff check django_strawberry_framework/filters/factories.py` — "All checks passed!" (only the standing COM812-vs-formatter advisory).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `filters/factories.py` checklist box in `docs/review/review-0_0_9.md`.

---

## Comment/docstring pass

Folded into the consolidated single-spawn above (the cycle's only edits are docstring/comment rewords; no separate logic pass exists to gate them).

### Per-finding dispositions

- Medium (forward-looking entry point unconsumed): resolved case (1) — reworded both docstrings + the module docstring closing sentence + the cache lead comment to the accurate deferred state, citing `spec-027` Non-goals (the real owning deferral) and `spec-030`'s explicit-sidecar consumer. No wiring forwarded (case (2) disproven).
- Low 1 (shallow-copy aliasing): deferred-with-trigger, no edit (trigger not fired).
- Low 2 (module docstring scope): edited — scoped the finalizer-materialization sentence to the BFS factory's input classes and noted Layer 6's classes are never module globals.
- DRY 1 / DRY 2: deferred-with-trigger, no edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

Comment edits describe the final (deferred) reality and remove the self-falsifying version pin. No TODO anchor added — the deferred consumer has no active owning slice (the standing Non-goal in spec-027 is the citation, not a live slice), and AGENTS.md/comment-dicta prefer dropping a forward-looking label over anchoring at no real slice. The spec-027 / spec-030 references use symbol-qualified `#"unique substring"` form per AGENTS.md.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Per `AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed" AND the active review plan's silence on changelog authorization for this cycle (no dispatch-prompt or artifact authorization; the dispatch explicitly says "record disposition in artifact" and "Do NOT update CHANGELOG.md"). The cycle's edits are docstring/comment-only — no consumer-visible behaviour change (the affected surface has zero source consumers at 0.0.9). Per-file cycles are NEVER the authorising scope and must forward genuine CHANGELOG drift to the project pass; there is no CHANGELOG drift here (no behaviour shipped or changed), so nothing to forward.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
