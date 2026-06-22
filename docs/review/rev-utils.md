# Review: `django_strawberry_framework/utils/`

Status: verified

Folder pass over the cross-cutting shared-substrate package consumed by every other folder. `utils/` is the bottom layer where the cross-family DRY resolutions LIVE: `inputs` (generated-input substrate), `input_values` (neutral set-input traversal), `permissions` (active-input permission core), `querysets` (visibility contract), `relations` (relation-shape classifier), `strings` (case conversion), `typing` (type unwrapping), `connections` (window-bound / sidecar contracts). All 8 in-scope files are individually `verified` this cycle; the `__init__.py` export surface is covered here per the folder-pass convention.

Per-cycle baseline `97dd05ca3edf47347c104de147342c22a73c613e`. `git diff 97dd05ca -- django_strawberry_framework/utils/` is empty, `git diff HEAD -- django_strawberry_framework/utils/` is empty, and `git log 97dd05ca..HEAD -- django_strawberry_framework/utils/` returns nothing — no commit touched `utils/` since baseline (last touch `7a17ba75`, the `model_for` promotion, predates the baseline). Dirty tree at review time was `docs/feedback2.md` + `docs/review/` scratchpads only (out of scope per AGENTS.md #34). Genuine no-source-edit folder pass (shape #5).

## DRY analysis

- None at the folder level — every cross-family DRY resolution that `utils/` exists to host is already single-sited, and the cross-sibling sweep finds no folder-level duplication to fold. Each of the 8 modules IS a consolidation point rather than a candidate: `inputs.py` (generated-input substrate serving filters/orders/mutations), `input_values.py` (neutral set-input traversal, 0.0.9 DRY Major-1), `permissions.py` (active-input permission core, 0.0.9 DRY Major-3), `querysets.py` (visibility contract, 0.0.9 DRY Major-1), `relations.py` (single-home relation-shape classifier), `strings.py` (single-home case conversion), `typing.py` (three orthogonal type-introspection contracts), `connections.py` (window-bound / sidecar-kwarg contracts). No symbol name is defined in two-or-more sibling files (verified: zero `def`/`class` name collisions across the 8 files), and the cross-sibling repeated-literal sweep finds no literal shared between two-or-more siblings (the only repeated literals are intra-file vocabularies — `relations.py`'s `RelationKind` `Literal` members / Django flag names, and `inputs.py`'s two collision-message tails — neither appears in any other utils file). Re-consolidating consolidation points is net-negative. Cross-family DRY items that pair a `utils/` substrate against its filter/order/mutation consumers are forwarded to the project pass, not held here (see `### Other positives`).

## High:

None.

## Medium:

None.

## Low:

### `__init__.py` re-export surface is bypassed by every production consumer (folder-level mirror of the per-file `instance_accessor` / `is_async_callable` asymmetry)

`utils/__init__.py` re-exports seven symbols at the package root (`__all__ = ("RelationKind", "is_many_side_relation_kind", "pascal_case", "relation_kind", "snake_case", "unwrap_graphql_type", "unwrap_return_type")`, sorted, no private leak) from three submodules (`relations`, `strings`, `typing`). Every first-party consumer of those symbols imports them **submodule-direct** instead of via the package root — `from ..utils.relations import relation_kind`, `from ..utils.strings import snake_case`, `from ..utils.typing import unwrap_graphql_type`, etc. across `filters/sets.py`, `orders/sets.py`, `types/*`, `optimizer/*`, `mutations/sets.py`, `sets_mixins.py`, `management/commands/inspect_django_type.py`. A package-wide grep for `from …utils import <symbol>` returns zero production hits; the only package-root import anywhere is `tests/utils/test_typing.py #"from django_strawberry_framework.utils import unwrap_graphql_type"` (one test).

This is the folder-level mirror of the two per-file Lows already recorded from the inverse angle: `rev-utils__relations.md` flags `instance_accessor` as NOT in `__all__` (consumed submodule-direct), and `rev-utils__typing.md` flags `is_async_callable` as NOT in `__all__` (consumed submodule-direct). Both per-file artifacts (and Worker 3) accepted those as consistent, non-finding, forward-looking. The folder view shows the convention is in fact "submodule-direct import for every relation/string/typing helper, whether or not it is in `__all__`" — the `__all__` re-export is exercised only by a single test, and `instance_accessor` / `is_async_callable` (submodule-only, omitted from `__all__`) are not anomalies but the dominant pattern. `unwrap_return_type` (in `__all__`) is no longer orphaned — its sole first-party caller `mutations/sets.py::_is_relay_id_annotation` landed in commit `ee1afb58` (closing the prior cycle's orphan-Low per its own trigger; recorded in `rev-utils__typing.md`), but that caller, too, imports submodule-direct (`from ..utils.typing import unwrap_return_type`).

Correct as-is and internally consistent: `__all__` is sorted, leaks nothing private, and matches the package docstring's named symbols; there is no drift between `__all__`, the docstring, and the (one) consumer that uses the root path. The asymmetry is harmless. Forward-looking, deferred: revisit the re-export surface only if a production consumer begins importing these helpers via the `utils` package root; at that point reconcile the convention in one direction — either promote `instance_accessor` / `is_async_callable` into `__all__` (so the root path is complete) or drop the unused re-exports (so the submodule path is the sole public surface). No action now. Forwarded to `rev-django_strawberry_framework.md` for one project-scope disposition of the `utils` public surface alongside the per-file asymmetries.

## What looks solid

### DRY recap

- **Existing patterns reused.** The folder is the package's DRY floor: every other folder reuses these substrates rather than re-spelling them. Confirmed single-sited and consumed widely at source — `relation_kind` / `is_many_side_relation_kind` / `instance_accessor` / `has_composite_pk` / `is_forward_many_to_many` (relations → optimizer/types/filters/orders/mutations); `snake_case` / `pascal_case` (strings → types/optimizer/filters/sets_mixins/mutations/management); `model_for` / `reject_async_in_sync_context` / `apply_type_visibility_*` / `SyncMisuseError` (querysets → connection/relay/types/mutations/permissions); `iter_active_fields` / `is_inactive_value` / `iter_input_items` / `SetInputTraversal` (input_values → filters/orders/permissions); `build_strawberry_input_class` / `materialize_generated_input_class` / `GeneratedInputArgumentsFactory` (inputs → filters/orders/mutations); `verbatim_path` / `active_permission_targets` / `request_from_info` (permissions → filters/orders/mutations); `derive_connection_window_bounds` / the sidecar-kwarg family (connections → optimizer/walker + connection). The `permissions.py:59` and `inputs.py:206` "from … import" lines a naive grep surfaces are **comments** (re-export note / cycle-dodge note), not imports.
- **New helpers considered.** None warranted at the folder level. The two per-file deferred helper candidates (`ClearSpec` in `inputs.py`, gated on a third eight-kwarg clear call site; a unified `unwrap(recursive=)` in `typing.py`, rejected as re-entangling three independent dimensions) are correctly held at the file level with explicit triggers. No new shared `utils/` helper is implied by the cross-sibling view — the modules already split cleanly by concern with no overlap.
- **Duplication risk in the current folder.** No symbol name is duplicated across the 8 files (zero `def`/`class` name collisions). No string literal is shared between two-or-more siblings — the only repeated literals are intra-file enumerated vocabularies (`relations.py` `RelationKind` members + Django flag names; `inputs.py` collision-message tails), each living in exactly one module and each dispositioned in its own per-file artifact as intentional sibling design. No folder-level literal-DRY candidate. The prior-cycle `_verbatim_path` → public `verbatim_path` promotion (commit `8d6ca99b`) is coherent: defined once in `permissions.py`, in `permissions.py.__all__`, used internally and by `orders/sets.py:362`, with zero `_verbatim_path` orphan anywhere in source/tests/examples.

### Other positives

- **One-way dependency direction confirmed at source — `utils/` is the bottom layer.** A targeted grep for any import from `filters` / `orders` / `mutations` / `types` / `optimizer` / `connection` / `list_field` / `relay` / `registry` / `scalars` / `sets_mixins` across all 8 files returns zero real imports (the single grep hit is a comment in `permissions.py`). The only upward import any utils module makes is `from ..exceptions import ConfigurationError` (`inputs.py:35`, `permissions.py:34`, `querysets.py:35`), and `exceptions.py` is a true leaf (imports nothing first-party). Every other import is stdlib (`dataclasses`, `typing`, `functools`, `inspect`, `importlib`, `collections.abc`), `strawberry`, or `django.db.models` / `django.http`. Utils imports NOTHING from any upper layer — the no-upward-import invariant holds package-wide.
- **Intra-utils DAG is acyclic and one-way.** The only first-party sibling edge inside the folder is `permissions.py → .input_values` (`permissions.py:35`, importing the shared traversal primitives + LEAF/RELATED markers), plus the three `__init__.py` re-export edges (`→ .relations`, `→ .strings`, `→ .typing`). `relations` / `strings` / `typing` / `querysets` / `connections` / `input_values` / `inputs` import no utils sibling. No cycle, no back-edge; the substrate that everyone consumes (`input_values`) sits below its sole sibling consumer (`permissions`).
- **`__init__.py` export surface is clean.** `__all__` is sorted alphabetically (verified), contains no private/`_`-prefixed symbol, and names exactly the seven symbols actually imported by `__init__.py`. The package docstring's `relations` / `strings` / `typing` bullets list the same re-exported symbols; the `inputs` / `permissions` / `input_values` / `querysets` bullets correctly describe those modules as dotted-path substrates (not re-exported), matching the absence of those symbols from `__all__`.
- **GLOSSARY coherence at the folder level.** The only utils symbol carrying a symbol-level GLOSSARY entry is `SyncMisuseError` (public, package-root `__all__`) at `#syncmisuseerror` (`docs/GLOSSARY.md:41/143/163/201/1115`), which the per-file `rev-utils__querysets.md` confirmed accurate (ConfigurationError+RuntimeError multi-inherit, closed coroutine before raise, single-sited `apply_type_visibility_sync` routing, types.relay back-compat re-export). The `is_async_callable` contract prose at `#djangolistfield:364` / `#djangomutationfield:396` is descriptive contract text (partial-aware / `__call__` / one-hop), accurate per `rev-utils__typing.md`. Every other utils symbol (relation/string/unwrap/input/permission/queryset helpers) is private/dotted-path and correctly carries no GLOSSARY entry — absence is correct, not drift.
- **All 8 per-file artifacts agree and are individually `verified`.** Each is itself a genuine shape #5 (empty per-file diff against its own baseline + HEAD; cumulative DRY work in HEAD). The folder view introduces no contradiction with any per-file disposition; the five files with only forward-looking Lows (`connections`, `input_values`, `inputs`, `relations`, `typing`) and the three with all-`None.` findings (`permissions`, `querysets`, `strings`) are consistent with the cross-file picture. The consolidation-point factoring held up branch-by-branch in every per-file review (SliceMetadata parity in connections, sync/async visibility parity in querysets, identity-based collision detection in inputs, exhaustive disjoint classification in relations/input_values/permissions, idempotency in strings, bounded recursion in typing).
- **Static-helper sweep complete.** Overviews exist under `docs/shadow/` for all 9 files including `__init__.py` (plan-time `--all` sweep, no source newer than its overview). The folder-pass repeated-literal and import-direction comparisons were driven off those overviews and re-confirmed at source.

### Summary

`utils/` is in clean, settled shape and correctly occupies the bottom of the dependency graph: it imports nothing from any upper subsystem (only `..exceptions`, a leaf, plus stdlib / strawberry / django), so the utils→no-upward-import invariant holds package-wide and was re-confirmed at source this cycle. The intra-folder DAG is acyclic and one-way (the sole sibling edge is `permissions → input_values`, with `input_values` correctly the lower substrate). The `__init__.py` export surface is sorted, leaks nothing, and matches the package docstring. No symbol name and no string literal is duplicated across the 8 files — every module is itself a single-source consolidation point, which is exactly why the folder-level DRY analysis is a single `None`. The cross-sibling repeated-literal sweep finds only intra-file vocabularies, each already dispositioned per-file. The one folder-level Low — the `__all__` re-export surface being bypassed by every production consumer in favor of submodule-direct imports — is the consistent dominant convention (mirroring the accepted per-file `instance_accessor` / `is_async_callable` asymmetries), harmless, and forward-looking, forwarded to `rev-django_strawberry_framework.md` for one project-scope disposition of the `utils` public surface. All 8 per-file siblings are `verified`; both diffs against baseline and HEAD are empty with no commits to `utils/` since baseline. Cross-family DRY (substrate-vs-consumer mirrors: filters/orders inputs family, apply-pipeline scaffold, permission-wrapper-layer mixin, Layer-6 cache primitives, mutations OPERATIONS verb vocabulary) is likewise forwarded to `rev-django_strawberry_framework.md`, kept NONE at folder level. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged` (COM812-vs-formatter advisory warning only; pre-existing, unrelated).
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- Genuine shape #5 folder pass. `git diff 97dd05ca3edf47347c104de147342c22a73c613e -- django_strawberry_framework/utils/` empty, `git diff HEAD -- django_strawberry_framework/utils/` empty, `git log 97dd05ca..HEAD -- django_strawberry_framework/utils/` returns nothing (no commit touched utils since baseline; last touch `7a17ba75` predates it). All 8 per-file siblings are `verified`.
- utils→no-upward-import invariant verified at source: the only upward import is `from ..exceptions import ConfigurationError` (`inputs.py:35`, `permissions.py:34`, `querysets.py:35`); `exceptions.py` is a no-first-party-import leaf. Zero imports from filters/orders/mutations/types/optimizer/connection/list_field/relay/registry/scalars/sets_mixins (the one grep hit at `permissions.py:59` is a comment, not an import).
- Intra-utils DAG acyclic/one-way: sole sibling edge `permissions.py:35 from .input_values import …`; `__init__.py` re-exports `.relations`/`.strings`/`.typing`. No back-edge, no cycle.
- `__init__.py` `__all__` sorted, no private leak, matches docstring. The folder-level Low (re-export surface bypassed by every production consumer; only `tests/utils/test_typing.py:9` uses the package-root path) is forward-looking and the consistent dominant convention — mirrors the accepted per-file `instance_accessor` (`rev-utils__relations.md`) and `is_async_callable` (`rev-utils__typing.md`) asymmetries; `unwrap_return_type` is no longer orphaned (caller `mutations/sets.py::_is_relay_id_annotation`, commit `ee1afb58`, also imports submodule-direct). No source-site TODO owed (gated on a future package-root consumer, not a staged slice). Forwarded to `rev-django_strawberry_framework.md`.
- No duplicated helper across the 8 files (zero `def`/`class` name collisions). Cross-sibling repeated-literal sweep (9 overviews): no literal shared between 2+ siblings; only intra-file vocabularies (`relations.py` RelationKind members + Django flags; `inputs.py` collision-message tails), each dispositioned per-file. `verbatim_path` promotion coherent, no `_verbatim_path` orphan.
- GLOSSARY: only `SyncMisuseError` carries a symbol-level entry (public, root `__all__`), accurate; `is_async_callable` contract prose at `#djangolistfield`/`#djangomutationfield` accurate. All other utils symbols private/dotted-path → no entry → absence correct. No GLOSSARY-only fix in scope.
- Cross-family DRY (substrate-vs-consumer mirrors) forwarded to the project pass `rev-django_strawberry_framework.md`, NOT held at folder level.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits. The `utils/__init__.py` module docstring (the per-submodule concern bullets, the 0.0.9-DRY-pass `docs/feedback.md` Major-1 references for `input_values` and `querysets`) is accurate against the implementation and the import graph — each named symbol exists in the named submodule, and the re-exported-vs-dotted-path distinction the docstring implies matches `__all__`. No stale TODOs at the folder level (per-file overviews confirm zero TODO comments in the 8 files). The per-file comment passes (all 8 siblings) already verified each module's internal comments and cross-module claims at source.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, or doc edits this cycle (empty diff against baseline and HEAD). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog edits for review-cycle artifacts), no changelog entry is warranted.

---

## Verification (Worker 3)

Terminal-verify of a genuine shape #5 no-source-edit folder pass. All three Worker 2 sections carry the `Filled by Worker 1 per no-source-edit cycle pattern.` gate line.

### Logic verification outcome

Zero-edit proof clean on all axes: `git diff 97dd05ca3edf47347c104de147342c22a73c613e -- django_strawberry_framework/utils/` empty; `git diff HEAD -- django_strawberry_framework/utils/` empty; `git log 97dd05ca..HEAD -- django_strawberry_framework/utils/` returns nothing; owned-paths `git diff --stat 97dd05ca -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty; `git diff -- CHANGELOG.md` empty. No sibling-cycle attribution needed (no dirty hunk touches any utils path or any owned path).

Folder reasoning independently confirmed at source (read-only):
- **No-upward-import invariant holds.** A grep for `from ..(filters|orders|mutations|types|optimizer|connection|list_field|relay|registry|scalars|sets_mixins)` across all 8 files returns ZERO hits. The only upward import is `from ..exceptions import ConfigurationError` at `inputs.py:35`, `permissions.py:34`, `querysets.py:32` (the artifact cites `querysets.py:35` — cosmetic line miscount, content-not-identifier #27; the import is present and verified). All other imports are stdlib / `strawberry` / `django`. `exceptions.py` is a leaf.
- **Intra-utils DAG acyclic/one-way.** The sole first-party sibling edge is `permissions.py:35 from .input_values import …`; `__init__.py` re-exports `.relations`/`.strings`/`.typing`. `relations`/`strings`/`typing`/`querysets`/`connections`/`input_values`/`inputs` make no utils-sibling import. No back-edge, no cycle; `input_values` sits below its sole sibling consumer `permissions`.
- **`__init__.py` export surface correct.** `__all__` is exactly the 7 named symbols (`RelationKind`, `is_many_side_relation_kind`, `pascal_case`, `relation_kind`, `snake_case`, `unwrap_graphql_type`, `unwrap_return_type`), sorted alphabetically, no private/`_`-prefixed leak, matching the three re-export lines and the docstring's named symbols.
- **No duplicated helper across the 8 files.** `def`/`class` name dedup across all 8 files returns empty (zero collisions).
- **GLOSSARY accurate.** Per-file siblings already verified `SyncMisuseError` (sole symbol-level entry, public root `__all__`) and the `is_async_callable` contract prose; every other utils symbol is private/dotted-path and correctly carries no entry. No GLOSSARY-only fix in scope (would be disqualifying for a #5; none present).

### DRY findings disposition

Folder-level DRY is a genuine `None`: every module IS a single-source consolidation point, zero symbol-name collisions, zero literal shared between 2+ siblings (the only repeated literals are intra-file vocabularies, each dispositioned per-file). Cross-family substrate-vs-consumer DRY items correctly forwarded to `rev-django_strawberry_framework.md` (project pass), not held at folder level — carried forward.

### Temp test verification

None — no temp tests needed for a no-source-edit folder pass.

### Low disposition

The single folder-level Low (`__all__` re-export surface bypassed by submodule-direct imports) is forward-looking and correctly forwarded to the project pass. Verified: ZERO production package-root imports (`from ..utils import <symbol>` / `from django_strawberry_framework.utils import <symbol>`) anywhere in `django_strawberry_framework/`; the package-root path is exercised only by tests. Minor note: the Low prose cites a single test (`tests/utils/test_typing.py`), but `tests/utils/test_relations.py:5` also imports via the package root — a cosmetic miscount (content-not-identifier #27) that does not change the disposition, since the load-bearing claim (zero PRODUCTION package-root consumers) holds. Not a reject trigger.

### Changelog disposition

`Not warranted`, both citations present (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" + active plan `review-0_0_11.md` silence). `git diff -- CHANGELOG.md` empty — consistent. Internal-only framing matches the diff scope (zero edits this cycle).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the utils/ folder-pass checklist box in `docs/review/review-0_0_11.md`. Carry-forward: cross-family substrate-vs-consumer DRY mirrors (filters/orders inputs family, apply-pipeline scaffold, permission-wrapper-layer mixin, Layer-6 cache primitives, mutations OPERATIONS verb vocabulary) and the `utils` public-surface asymmetry Low all owed to the project pass `rev-django_strawberry_framework.md`.
