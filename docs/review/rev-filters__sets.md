# Review: `django_strawberry_framework/filters/sets.py`

Status: verified

Scope: single-file logic review of `FilterSet` + `FilterSetMetaclass` — declaration,
Meta validation, and the sync/async apply pipeline. Shipped 0.0.8; this artifact
supersedes the stale 0.0.7 `rev-filters__sets.md` that pre-existed on disk (active
plan box was unchecked). Source last reviewed/verified at 0.0.7; re-reviewed fresh
against the live 0.0.9 source. Cross-file concerns (shared mixins in `sets_mixins.py`,
shared permission/input-value cores in `utils/`) are flagged as folder/project-pass
follow-ups, not local defects.

## DRY analysis

- **`_normalize_input` operator-bag filter lookup is a redundant double `.get`.** In
  the per-field operator-bag branch, `sets.py::_normalize_input #"all_filters.get(form_key) or all_filters.get("`
  (source ~739-741) computes `form_key` as `base_path` when `django_lookup == "exact"`
  else `f"{base_path}__{django_lookup}"`, then falls back to
  `all_filters.get(f"{base_path}__{django_lookup}")`. For every non-`exact` lookup the
  two `.get` keys are byte-identical (the `or` second arm can never differ); only the
  `exact` case actually probes a second key (`base_path` then `base_path__exact`).
  Collapse to a single lookup that tries `base_path` first then the suffixed key only
  for `exact` (or build the candidate key list once). Act-now: it is a localized
  simplification with no behavior change (the redundant arm returns the same object).
  Single call site, so no shared-helper extraction — an inline tidy.

- **Defer: the three logical-branch walkers (`and`/`or`/`not`) are spelled three times
  across `_run_permission_checks`, `_evaluate_logic_tree`, and
  `_collect_nested_visibility_querysets_async`.** Source 1211-1239 (perm),
  1418-1452 (Q-build), 1064-1091 (async pre-walk). Each independently does
  "`and`-list loop, `or`-list loop, `not`-single" with a different per-branch action
  (recurse perm-check / `&=` `|=` `~&` a `Q` / await a visibility derive). A shared
  `_for_each_logic_branch(tree, on_and, on_or, on_not)` driver could host the iteration
  shape. Defer until a fourth logical-branch consumer lands OR the branch set changes
  (e.g. a `xor`/`nand` arm): today the per-branch actions differ enough (sync vs async,
  `Q` algebra vs side-effecting recursion) that a callback-threaded extraction is
  net-negative readability. The `_LOGIC_KEYS` source-of-truth and the wire-key strings
  (`"and"`/`"or"`/`"not"`) are already single-sited in `inputs.py`; only the iteration
  skeleton repeats.

- **Defer: the sync/async visibility-derive twin
  (`_derive_related_visibility_querysets_sync` / `_async`, source 954-1003) is the same
  deliberate sibling pattern this package treats as intentional.** Both share
  `_iter_visibility_steps` for the pre-await state; only the `apply_type_visibility_*`
  call and the child `apply_sync`/`apply_async` await differ. Do NOT extract — the
  await-unwrap makes a single-body collapse net-negative (same calibration as
  `relay.py`/`list_field.py` sync/async twins). No trigger; recorded so a future DRY
  cycle does not re-flag it.

## High:

None.

## Medium:

None.

## Low:

### `_normalize_input` operator-bag double `.get` (also in DRY analysis)

`sets.py::_normalize_input #"all_filters.get(form_key) or all_filters.get("` (source
~739-741). The `or`-fallback `.get` is dead for every non-`exact` lookup because
`form_key` already equals the fallback key; only `exact` benefits from the second probe.
Harmless (the second arm returns the identical filter instance or `None`), but it reads
as if two distinct keys are meaningfully tried. Recommended: probe `base_path` then the
suffixed key explicitly, or build a 1-or-2-element candidate list. Localized
simplification; no test change required (behavior is identical), so it is a maintainability
Low rather than a correctness fix.

### `get_filters` single-threaded reentrancy flag — documented, forward-looking

`sets.py::get_filters` uses a class-level `_is_expanding_filters` flag (via
`expanded_once`) rather than a `threading.local`. The docstring (source 313-326) already
spells out the contract: expansion runs single-threaded during `finalize_django_types()`
and once per class for the registry lifetime, and parallel test threads that hit the same
FilterSet may race to the unexpanded `super().get_filters()`. This is correct today and
explicitly documented with a "do not introduce `threading.local` without a real consumer
path" guard. Defer until a real multi-threaded `get_filters()` consumer path appears;
then re-triage thread-locality. No edit now.

### `GlobalIDMultipleChoiceFilter` `**default.extra` forward — verified safe, documented

`filter_for_field` (source 498-502) forwards `**default.extra` from the upstream SCALAR
PK filter into `GlobalIDMultipleChoiceFilter`. The inline comment (485-497) justifies why
this is safe: the multi-choice filter backs onto `_GlobalIDMultipleChoiceField` (a plain
`MultipleChoiceField`, not model-backed), so it needs no `queryset=` and the scalar
default's `.extra` carries no incompatible `ModelChoiceField` kwargs. Confirmed against
`filters/base.py::_GlobalIDMultipleChoiceField` (source 324-358: subclasses
`MultipleChoiceField`, no queryset requirement). No finding — recorded so a future reviewer
who narrows `_GlobalIDMultipleChoiceField`'s field contract knows this forward depends on
it staying queryset-free.

## What looks solid

### DRY recap

- **Existing patterns reused.** The 0.0.9 DRY consolidation is fully realized here:
  metaclass declaration collection via `sets_mixins.collect_related_declarations`
  (source 177-184); the expansion cache + reentry guard via `sets_mixins.expanded_once`
  (source 368-374) with the lifecycle attr names single-sourced through
  `_lifecycle: SetLifecycleAttrs` (246-250); the active-input traversal via
  `utils/input_values.iter_active_fields` + `SetInputTraversal` (700-706); the per-field /
  per-branch permission core via `utils/permissions.run_active_input_permission_checks`
  (1199-1206), with `_iter_input_items` / `_request_from_info` /
  `_iter_active_related_branches` / `_extract_branch_value` / `_invoke_permission_method` /
  `_active_permission_field_paths` all thin family-named delegates to `utils/permissions.py`.
  `_form_key_for_python_attr` is backed by the import-time-built `_FORM_KEY_BY_PYTHON_ATTR`
  reverse map (O(1) vs O(n) scan, 85-88). `_apply_common_prelude` / `_apply_common_finalize`
  (1628-1669) factor the shared apply sequence out of `apply_sync` / `apply_async`.
- **New helpers considered.** A logic-branch iteration driver and a single-body
  sync/async visibility derive — both evaluated and DEFERRED in `## DRY analysis` with
  triggers / intentional-twin reasoning. No new helper warranted at this granularity now.
- **Duplication risk in the current file.** `_raise_logic_depth_exceeded` (1006-1018)
  already single-sources the depth-cap `ConfigurationError` across its three callers
  (`_collect_nested_visibility_querysets_async`, `_run_permission_checks`,
  `_evaluate_logic_tree`). The `and`/`or`/`not` wire strings are local literals but their
  canonical source is `_LOGIC_KEYS` in `inputs.py`; the repeated `"related_filters"`
  literal (6x per the shadow overview) is the `collection_attr` / `related_attr` argument
  threaded to the shared collectors and is intentional (it names a Django-filter-managed
  attribute, not a package constant). The sync/async visibility twin is deliberate sibling
  design (calibration carried from prior cycles).

### Other positives

- **Metaclass collection correctness.** `FilterSetMetaclass.__new__` (153-186) calls
  `super().__new__` BEFORE collecting related filters, and `collect_related_declarations`
  runs with `inherit_from_bases=False` because `django_filters`'s metaclass already
  MRO-merges `declared_filters` — only the `isinstance(RelatedFilter)` filter runs, so no
  double-merge. The `filter_fields` -> `fields` Meta alias (162-168) is gated on
  `not hasattr(meta_class, "fields")` so an explicit `fields` is never clobbered.
- **`get_filters` cycle safety.** The `cls.__dict__`-direct guard read (not `getattr`)
  is load-bearing for two reasons the docstring enumerates: a subclass must not inherit a
  parent's completed cache via MRO, and the in-flight class (created mid-metaclass before
  `related_filters` is stamped) must not cache a half-built result. The cache-write guard
  (355-359) correctly requires BOTH `related_filters in cls.__dict__` AND every
  `_filterset` resolved to a real class (no leftover string forward refs), so a circular
  same-module `RelatedFilter` neither caches prematurely nor blows the stack.
- **Meta validation / `get_fields` narrowing.** Per-field `"__all__"` expansion
  (405-418) runs before the mutually-exclusive top-level `"__all__"` branch (`meta_fields`
  is either the string or a dict, never both). The own-PK-under-Relay narrowing drops
  ordering/pattern lookups to `exact`/`in`/`isnull` so a GlobalID PK never emits a corrupt
  `String` input (spec-027 H1). The `model is None` guard (423-429) is honestly marked
  `# pragma: no cover` as a forward-defensive no-op because `super().get_fields()` already
  raises `AttributeError` first for that shape — consistent with AGENTS.md's pragma rule
  (genuinely unreachable under the runner, not a workaround).
- **Decision-4 Relay-vs-scalar conditional.** `filter_for_field` / `filter_for_lookup`
  are the single source of shape derivation (the factory derives from resolved filter
  instances, not a parallel map). `_is_own_pk_under_relay_owner` (559-582) is correctly
  inert pre-binding (`_owner_definition is None` -> `False`) so package-internal pre-finalize
  tests keep the upstream shape, and authoritative post-phase-2.5. `filter_for_lookup`
  RAISES `ConfigurationError` (546-550) for an unsupported own-PK GlobalID lookup named in
  an explicit `Meta.fields` list rather than silently emitting a corrupt input.
  `_resolve_relation_target_type` reads `.origin` (not `.type`/`.type_cls`) off the
  definition, with an inline comment recording that a stale `.origin` read previously
  dropped every owner-aware resolution to the registry fallback — the right contract is
  pinned.
- **Sync vs async apply pipeline.** Both paths share `_apply_common_prelude` /
  `_apply_common_finalize`; `apply_async` adds exactly two async-only steps —
  `_derive_related_visibility_querysets_async` (top-level await) and
  `_collect_nested_visibility_querysets_async` (the nested pre-walk keyed by
  `id(child_input)`). The pre-walk solves a real ordering hazard: `_q_for_branch`'s sync
  derive would raise `SyncMisuseError` mid-`.qs` for an async-only target `get_queryset`,
  so the async path pre-derives every reachable branch's visibility map and threads it
  through `_nested_qs_by_branch_id`; `_q_for_branch` consults it by object identity and
  falls back to the sync derive only when a consumer short-circuits the walker. The
  `id()`-identity key is sound because `_normalize_input` copies the child sub-trees
  verbatim into `self.data` (the LOGIC branch at 707-709), preserving object identity
  across the `.qs` boundary. `_apply_common_finalize` (perm check + form validate + `.qs`
  read) is wrapped once in `sync_to_async(thread_sensitive=True)` so a consumer's blocking
  `check_*_permission` / `method=` body / leaf ORM does not block the event loop.
- **Per-field permission gates, active-input-only scope.** Confirmed against the shared
  core: `run_active_input_permission_checks` (`utils/permissions.py:220-259`) fires
  `check_<field>_permission` once per SOURCE field (lookup-free, via
  `_active_permission_field_paths`), recurses into each active `RelatedFilter` branch's
  child filterset via `target_attr="filterset"` (own class, own bare, own per-class dedup
  set inside the shared `_fired` map), and fires the parent per-branch gate once — the
  intentional parent-vs-child double dispatch. The filter-only logical `and`/`or`/`not`
  recursion (1208-1239) reuses the same `bare` and `_fired` so a gate fires at most once
  per class regardless of how many sibling arms reference it (the `or:[{shelves:...},
  {shelves:...}]` dedup case). Depth-capped at `_MAX_LOGIC_DEPTH`. Inactive branches
  (`UNSET`/`None`) are skipped end-to-end so an empty filter never pre-constrains the
  parent.
- **Tree overrides + `get_queryset`/optimizer composition.** `filter_queryset` (1341-1388)
  reads logical keys off `self.data` (not `cleaned_data`, which drops the non-form
  `and`/`or`/`not` slots — correctly documented) and composes the tree `Q` on top of the
  inherited leaf-clause `super().filter_queryset`. The depth / `info` / nested-map hand-off
  channels (`_logic_depth` / `_apply_info` / `_nested_qs_by_branch_id`) are threaded on
  sibling instances precisely because django-filter's `.qs` machinery cannot carry kwargs
  through — a real constraint, honestly worked around. `_apply_related_constraints`
  (1536-1626) keys the parent restriction off `related_filter.field_name` (the ORM path)
  not the declared attr name (the divergence case is documented), wraps as
  `pk__in=<parent-pk subquery>` to collapse many-side duplicates WITHOUT `.distinct()`
  (which would mutate consumer-visible queryset state), and surfaces a typed
  `ConfigurationError` for the mixed-base-model `&` case instead of Django's opaque
  `TypeError`. The `is`-identity model comparison correctly mirrors Django's own
  `Query.combine`.
- **`apply` dispatcher.** Catches the typed `SyncMisuseError` (a `ConfigurationError`/
  `RuntimeError` subclass) and rethrows `RuntimeError` with the actionable "use apply_async
  instead" message via `from exc` — class-based dispatch, no substring-matching against a
  string constant, and no duplicate cause-`str()` in the message (chain prints it once).
- **GLOSSARY drift quick-check — clean.** `#filterset` (GLOSSARY 464-474), `#relatedfilter`
  (994-998), the `check_*_permission` active-input-only scope and `RelatedFilter(queryset=)`
  filter-scope-not-security-boundary prose, `#metafilterset_class` (670-683), and the
  `apply_sync`/`apply_async` resolver-API description all read accurately against the live
  source. The `SyncMisuseError` entry's "[`FilterSet.apply`]'s sync dispatcher rewraps"
  prose (1276) matches `apply` at source 1747-1771. No drift; no GLOSSARY edit in scope.

### Summary

Logic-clean, declaration-and-pipeline-complete file at 0.0.9. The metaclass collection,
cycle-safe `get_filters` cache/guard, Meta `"__all__"` narrowings, Decision-4
Relay-vs-scalar conditional, active-input-only permission gating with parent/child double
dispatch, the sync/async apply twin with the `id()`-keyed nested-visibility pre-walk, and
the duplicate-collapsing related-constraint subquery are all correct and well-documented;
the heavy comment load is load-bearing (it pins non-obvious django-filter `.qs`-boundary
and ORM-JOIN-duplication contracts). No High, no Medium. One actionable Low (a redundant
double `.get` in the operator-bag branch — a localized no-behavior-change tidy) plus two
recorded-intent / forward-looking Lows (single-threaded `get_filters` flag; the verified-safe
`**extra` forward). Because the one act-now Low recommends a real (if trivial) source edit,
this does NOT collapse to shape #5 — routed standard `under-review` for Worker 2.

---

## Fix report (Worker 2)

Consolidated single-spawn: one act-now Low (a trivial, semantics-preserving simplification
of the operator-bag filter lookup) plus two forward-looking Lows that need no edit. The lone
edit is logic-adjacent (touches executable lines) but byte-for-byte behavior-preserving, the
existing docstrings/comments already match the post-edit behavior, and no disposition depends
on Worker 3 blessing the logic first — so it qualifies for the consolidated shape.

### Files touched
- `django_strawberry_framework/filters/sets.py:735-744` (`_normalize_input`, operator-bag
  branch) — collapsed the redundant double `.get`. Old: `form_key` was computed, then
  `filter_instance = all_filters.get(form_key) or all_filters.get(f"{base_path}__{django_lookup}")`.
  New: bind `suffixed_key = f"{base_path}__{django_lookup}"` once, keep `form_key` unchanged
  (`base_path` for `exact`, else `suffixed_key`), then `filter_instance = all_filters.get(form_key)`
  with a guarded second probe `if filter_instance is None and form_key != suffixed_key:`.

### Why the semantics are identical
- **Non-`exact` lookups:** `form_key == suffixed_key`, so the original `get(form_key) or get(suffixed_key)`
  is `get(suffixed_key) or get(suffixed_key)` — the second arm can only return the same object
  (or `None`) the first already produced; net result `get(suffixed_key)`. New code: the
  `form_key != suffixed_key` guard is False, so the second probe never runs; net result
  `get(form_key) == get(suffixed_key)`. Identical.
- **`exact` lookup (the one case the two keys genuinely differ):** `form_key == base_path`,
  `suffixed_key == f"{base_path}__exact"`. Original: `get(base_path) or get(base_path__exact)` —
  probes the bare key first, then the explicit `__exact` key. New: `get(base_path)`; if `None`
  and (always-true) `base_path != base_path__exact`, then `get(base_path__exact)`. Same two
  keys, same probe order. Preserved.
- **`or` → `is None` is safe:** `all_filters` values are `django_filters` `Filter` instances
  (always truthy — no `__bool__`/`__len__` override) or absent. The only falsy outcome of either
  `.get` is `None` from a missing key, so `X or Y` and `X if X is not None else Y` coincide. The
  `is None` form additionally matches the immediately-following `if filter_instance is None:` guard
  (sets.py:742) and the LEAF-branch lookup at sets.py:757.
- `form_key` is unchanged, so every downstream use (`data[form_key]`, `field_name=form_key`,
  the `data.update`/`data[form_key]` writes) is untouched.

### Tests added or updated
- None. The artifact's Low explicitly states behavior is identical so no test change is required.
  Existing live coverage already exercises both arms through real GraphQL queries against the
  operator-bag path (`examples/fakeshop/test_query/test_scalars_filter_api.py`, exact + suffixed
  lookups), plus package-internal `tests/filters/test_sets.py` / `tests/filters/test_inputs.py`.
  A pure semantics-preserving simplification on an already-covered line warrants no new pin.

### Validation run
- `uv run ruff format .` — pass, no changes (265 files unchanged).
- `uv run ruff check --fix .` — pass, all checks passed (standing COM812-conflict warning only).
- No pytest (AGENTS.md / role rule). `uv.lock` not touched by `git status`.

### Notes for Worker 3
- Shadow file used: `docs/shadow/django_strawberry_framework__filters__sets.overview.md` (overview
  only; no `.stripped.py` line cites). Source line numbers above are canonical (live source).
- Diff is **logic-bearing** (touches executable lines) but semantics-preserving — re-check should
  confirm the `exact` two-key probe order and the non-`exact` single-key collapse per the
  equivalence argument above.
- Other dirty files in `git status` (`conf.py`, `exceptions.py`, `filters/factories.py`,
  `list_field.py`, `docs/GLOSSARY.md`, other `rev-*.md`, etc.) are concurrent other-worker /
  maintainer work, out of scope (AGENTS.md #33); not reverted, not mine.
- The two forward-looking Lows (`get_filters` single-threaded reentrancy flag; the verified-safe
  `GlobalIDMultipleChoiceFilter **default.extra` forward) and the two deferred DRY items
  (3x logic-branch walker skeleton; sync/async visibility twin) stay forward-looking — no edit.

---

## Verification (Worker 3)

### Logic verification outcome
The lone edit (`_normalize_input` operator-bag branch, source 735-745) is provably
semantics-preserving — verified independently, not trusted:

- **`or` → `is None` equivalence.** Confirmed `all_filters = cls.get_filters()` (source
  686) returns `django_filters` `Filter` instances or absent keys. Live scan
  (`config.settings` django setup): ZERO `__bool__`/`__len__` overrides across the entire
  upstream `Filter` hierarchy AND the package's own `filters/base.py` + `filters/inputs.py`
  `Filter` subclasses; `bool(Filter())` is `True`. So the only falsy `.get` outcome is
  `None` from a missing key, and `X or Y` ≡ `X if X is not None else Y` exactly.
- **Probe order + count, all cases.** Exhaustive temp harness (768 combinations =
  6 lookups × full power set of the 7 candidate keys, including `exact`/`title`/`title__exact`
  populated with DISTINCT filter objects): old `get(form_key) or get(suffixed_key)` vs new
  `get(form_key)` + guarded `get(suffixed_key)` produced IDENTICAL `(form_key, resolved
  filter)` in every case — 0 mismatches. Non-`exact`: `form_key == suffixed_key`, guard
  `form_key != suffixed_key` is False → single lookup (old `or` second arm was dead, returned
  the same object). `exact`: `form_key = base_path`, `suffixed_key = base_path__exact`, differ
  → both probed in the same bare-then-suffixed order as the old `or`. Confirmed.
- **`form_key` unchanged downstream.** Source 742 binds `form_key` to the same value as before
  (`base_path` for `exact`, else `suffixed_key`); the `data[form_key]` (747), `field_name=form_key`
  (752), `data.update`/`data[form_key]` (757) writes are byte-identical. No other executable line
  touched.

No input divergence found → semantics provably identical, not merely plausible. High 0 / Med 0.
The two forward-looking Lows (`get_filters` single-threaded reentrancy flag; verified-safe
`GlobalIDMultipleChoiceFilter **default.extra` forward) correctly stayed forward-looking.

### DRY findings disposition
Act-now Low (operator-bag double `.get`) FIXED + commented inline. The two deferred DRY items
(3x logic-branch walker skeleton; sync/async visibility twin) stayed forward-looking with
triggers / intentional-twin reasoning intact — no edit. Correct.

### Temp test verification
- Temp test: `docs/review/temp-tests/filters_sets/probe_equiv.py` — exhaustive old-vs-new
  key-probe equivalence (768 combinations, 0 mismatches).
- Disposition: deleted. A pure semantics-preserving simplification on an already-covered line
  (existing live `examples/fakeshop/test_query/test_scalars_filter_api.py` exercises exact +
  suffixed lookups) warrants no permanent pin; agree with Worker 2's no-test-change call.

### Comment verification
The new 5-line inline comment (source 737-741) accurately describes the final behavior — the
`exact`-probes-both vs every-other-lookup-coincides asymmetry — and replaces the silent dead
`or` arm with an explicit guard. Not a restatement of obvious code; pins a non-obvious
django-filter form-key registration fact. Surrounding operator-bag commentary unchanged and
still accurate. In scope.

### Changelog verification
`git diff -- CHANGELOG.md` empty. State "Not warranted" cites BOTH AGENTS.md #21 and the active
plan's silence on changelog authorization for this per-file cycle. Diff scope is internal-only
(a semantics-preserving lookup collapse, no public-API surface change), so "Not warranted" is the
correct state. Accepted.

### Sibling-cycle attribution
Owned-path `--stat` (vs `0872a20f`): `sets.py | 16` is this cycle. The other source hunks attribute
to CLOSED sibling cycles — `conf.py` (verified, [x] review-0_0_9.md:70), `exceptions.py` ([x] :72),
`list_field.py` ([x] :73), `filters/factories.py` ([x] :80) — and the 1-line `docs/GLOSSARY.md`
hunk to a closed sibling cycle. CHANGELOG.md diff empty. None are a rejection trigger.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

The diff is provably semantics-preserving (768-case exhaustive equivalence + zero-truthiness-override
proof), so the cycle-closing re-check can be light.

---

## Comment/docstring pass

(Folded into the consolidated single-spawn.)

### Files touched
- `django_strawberry_framework/filters/sets.py:736-740` — added a 5-line inline comment on the
  new `suffixed_key`/`form_key` block explaining the `exact`-probes-both vs. every-other-lookup-
  coincides asymmetry that the old dead `or` arm had silently obscured. No other comment in scope
  needed changing — the surrounding operator-bag commentary (715-732) still describes the final
  behavior accurately.

### Per-finding dispositions
- Low 1 (operator-bag double `.get`): FIXED + commented (above).
- Low 2 (`get_filters` single-threaded reentrancy flag): forward-looking per Worker 1; the
  existing docstring (sets.py:313-326) already documents the contract and the
  "no `threading.local` without a real consumer" guard. No comment edit.
- Low 3 (`GlobalIDMultipleChoiceFilter **default.extra` forward): no-finding / verified-safe per
  Worker 1; the existing inline comment (sets.py:485-497) already justifies it. No comment edit.
- DRY (3x logic-branch walker skeleton; sync/async visibility twin): deferred / intentional-twin
  per Worker 1. No edit.

### Validation run
- `uv run ruff format .` — pass, no changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
Comment is co-located with the logic edit; describes the final approved behavior. The two
forward-looking Lows and both DRY items stayed forward-looking.

---

## Changelog disposition

### State
Not warranted.

### Reason
The cycle's only edit is a semantically-equivalent internal simplification (a redundant double
`.get` collapsed to a single guarded lookup, behavior byte-identical) — no consumer-visible
change. Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed"), and the
active plan does not authorise a CHANGELOG edit for this per-file cycle (a per-file pass is never
the authorising scope; any drift forwards to the project pass). Both citations apply.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass, no changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log

### Fix report (Worker 2, pass 2)

Follow-up fix surfaced by the final test-run gate: the earlier cycle's
operator-bag simplification (`sets.py:742-745`) dropped full-suite coverage to
**99.98%** with the single missed line **`filters/sets.py:745`** (the
`if filter_instance is None and form_key != suffixed_key:` suffixed-key fallback
probe). `fail_under=100` gates, so this is a regression. Pre-review the
equivalent `or`-fallback arm was hit; the explicit-guard rewrite is clearer but
left line 745 unexercised by the existing suite.

#### REACHABLE-vs-UNREACHABLE determination: **REACHABLE** (proven)

Line 745 fires only when `django_lookup == "exact"` (so `form_key` = bare
`base_path`, `suffixed_key` = `base_path__exact`, the two differ) AND
`all_filters.get(base_path)` is `None`. I proved this is reachable via a valid
FilterSet config:

- **django-filter's exact-key registration** has TWO paths.
  `BaseFilterSet.get_filter_name` (`.venv/.../django_filters/filterset.py:313-326`)
  strips the trailing `__exact` from *generated* exact filters, so an autogen
  exact filter always registers under the **bare** `field_name` — for that path,
  `all_filters.get(base_path)` is never `None`, and 745 would be dead.
- **BUT** `BaseFilterSet.get_filters` ends with
  `filters.update(cls.declared_filters)` (`filterset.py:378`), which merges a
  declaratively-attached filter under its **literal class-attribute name**. A
  consumer who writes `name__exact = CharFilter(field_name="name", lookup_expr="exact")`
  on the FilterSet (instead of using `Meta.fields`) gets `all_filters` keyed
  **`name__exact`** with **no bare `name`** entry.
- The package's operator-bag builder groups that filter under
  `top_name="name"` (`inputs.py::_build_input_fields`, rpartition at lines
  644-652), and since `"name"` is NOT a `declared_filters` key (the declared key
  is `"name__exact"`), `django_source_path = sample_filter.field_name = "name"`
  (lines 737-740). So at runtime `base_path="name"`, `form_key="name"` (exact),
  `suffixed_key="name__exact"`: line 743 `all_filters.get("name")` → `None`,
  the line-744 guard is True, and **line 745** `all_filters.get("name__exact")`
  resolves the declared `CharFilter`.

Proof: an instrumented `trace.Trace` probe over a `name__exact`-declaring
`FilterSet` (model `Category`, `Meta.fields = []`) driving `_normalize_input`
showed line 745 executed **once** and produced the correct
`{"name": "foo"}`. The line is genuinely reachable through a real (if
unusual) declarative config — NOT dead code — so the explicit-guard form is
kept and the coverage is earned with a real test. Removing 744-745 would have
broken this config (the declared `__exact` filter would never normalize, falling
through to the raw-passthrough at 746-747 under the wrong assumption).

#### Test placement

Package-internal `tests/filters/test_sets.py` (not a live fakeshop query): no
existing example FilterSet declares an explicit `<field>__exact`, so a live
route would require NEW example model + DjangoType + schema wiring + a live
query, OR mutating an existing example FilterSet's GraphQL input surface
(broadly perturbing other live tests) — disproportionate for a package-internal
normalizer resolution line. The behavior under test is the operator-bag
normalizer's declared-key-vs-`field_name` resolution, which is exactly the
contract the sibling `_normalize_input` operator-bag unit tests already pin in
this same file (`test_normalize_input_operator_bag_dict_value_merges_into_form_data`
declares `lifetime_fines_cents__range = RangeFilter(...)` with `Meta.fields = []`
in the identical shape).

### Files touched
- `tests/filters/test_sets.py` — added
  `test_normalize_input_operator_bag_exact_resolves_explicit_suffixed_key`
  (placed before `test_normalize_input_top_level_range_filter_merges_positional_keys`).
  Declares `name__exact = CharFilter(field_name="name", lookup_expr="exact")`
  with `Meta.fields = []` so `get_filters()` carries only `name__exact`, asserts
  that, then drives `_normalize_input({"name": _NameBag(exact="foo")})` and
  asserts `{"name": "foo"}` — exercising the line-745 suffixed-key fallback.
- `django_strawberry_framework/filters/sets.py` — **no change** (the explicit
  guard at 742-745 is correct and now covered; the comment at 737-741 already
  describes the exact-probes-both asymmetry accurately).

### Validation run
- `uv run ruff format .` — pass, no changes (265 files unchanged).
- `uv run ruff check --fix .` — pass, all checks passed (standing COM812
  formatter-conflict warning only).
- Focused coverage: `uv run pytest tests/filters/test_sets.py
  --cov=django_strawberry_framework.filters.sets --cov-report=term-missing` —
  new test passes; `filters/sets.py` Missing list is `408-418, 484-498, 580,
  1122, 1449` (covered by other suite files in the full run) and **`745` is NOT
  in the missing list** — the regression line is now covered. `trace.Trace`
  probe independently confirmed line 745 executes once on the new test's path.
- No full `uv run pytest` (focused-only per dispatch). `uv.lock` clean (not
  touched by `git status`).

### Notes for Worker 3
- Diff is **logic/test-bearing**: a new test plus a determination that the
  explicit-guard lines 742-745 are REACHABLE (not dead) — re-verify by reading
  django-filter `BaseFilterSet.get_filters` `filters.update(cls.declared_filters)`
  (`.venv/.../django_filters/filterset.py:378`) and `get_filter_name`'s
  `__exact`-strip (313-326), and confirm the new test's
  `get_filters()` returns `["name__exact"]` (no bare `name`).
- No source edit: the earlier cycle's explicit-guard rewrite is preserved as-is;
  this pass only earns the coverage with a real test proving the genuine
  two-key-differ path.
- Changelog: Not warranted — test-only addition, zero consumer-visible change;
  AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") plus
  the active plan's silence on changelog authorization for this per-file
  follow-up. No `CHANGELOG.md` edit.

### Verification (Worker 3, pass 2)

`cycle accepted; verified` — coverage-regression follow-up holds. Box review-0_0_9.md:82
stays `[x]`; top-level `Status: verified`.

**Source unchanged this pass (test-only fix confirmed).** `git diff <baseline> --
django_strawberry_framework/filters/sets.py` is exactly the pass-1 logic-accepted edit
(the +16/-6 form_key collapse + 5-line comment, lines 736-745); NO new source hunk this
pass. No commit since baseline (`git log <baseline>..HEAD` empty for both owned paths);
both are working-tree mods. The explicit guard at 742-745 is byte-identical to the
pass-1 verified state. Only new change vs baseline = the new test in
`tests/filters/test_sets.py` (+40).

**REACHABILITY independently re-confirmed (W2 judged correctly — 745 is live, not dead).**
Read django-filter directly: `BaseFilterSet.get_filter_name` (`.venv/.../django_filters/
filterset.py:313-326`) strips the trailing `__exact` from *generated* exact filters (they
register under the bare field name), and `get_filters` (`:378`) ends with
`filters.update(cls.declared_filters)`, merging a declaratively-attached filter under its
literal class-attribute name. So a FilterSet that writes
`name__exact = CharFilter(field_name="name", lookup_expr="exact")` with `Meta.fields = []`
yields `all_filters` keyed `name__exact` with NO bare `name` entry. At runtime the
operator-bag branch computes `base_path="name"`, `form_key="name"` (exact),
`suffixed_key="name__exact"` → line 743 `get("name")` is `None` → line-744 guard
(`is None and form_key != suffixed_key`) is True → **line 745** `get("name__exact")`
resolves the declared filter. Genuinely reachable through a valid (if unusual) config; NOT
the removal case.

**Independent probe (own `uv run python`, config.settings, model `Category`):** built the
`name__exact`-declaring `WeirdCategoryFilter`, confirmed `get_filters()` returns exactly
`['name__exact']` (no bare `name`), drove the REAL `_normalize_input({"name":
_NameBag(exact="foo")})` → `{"name": "foo"}`. Then confirmed the bare-key probe misses
(`all_filters.get("name") is None`), so 745 is the resolving line — without it
`filter_instance` stays `None` and the bag object falls through to raw passthrough
(`data["name"] = _NameBag(...)`), which the test's `assert data == {"name": "foo"}` would
catch. Test is genuine, not a contrived no-op; it fails if 745's logic were wrong.

**Test placement / style:** `tests/filters/test_sets.py`, immediately before
`test_normalize_input_top_level_range_filter_merges_positional_keys`, mirroring the sibling
`test_normalize_input_operator_bag_dict_value_merges_into_form_data` (declarative filter +
`Meta.fields = []`, same `_normalize_input` driving shape). Package-internal placement is
AGENTS.md-justified: no live fakeshop FilterSet declares an explicit `<field>__exact`, so a
live `/graphql` route would need new example model + DjangoType + schema wiring or a
broadly-perturbing mutation of an existing input surface — disproportionate for a
package-internal normalizer-resolution line; the contract under test is package-internal
declared-key-vs-`field_name` resolution.

**Focused coverage:** `uv run pytest tests/filters/test_sets.py -k "...operator_bag..."
--cov=django_strawberry_framework.filters.sets --cov-report=term-missing` — 7 passed;
`filters/sets.py` Missing list does NOT include **745** (other Missing lines are covered by
the full suite; the focused-subset coverage FAIL is the expected `-k` artifact, not a
regression).

**Changelog / ruff / sibling attribution:** `git diff -- CHANGELOG.md` empty → Not-warranted
correct (test-only, zero consumer-visible change, both AGENTS.md #21 + active-plan-silence
cited). `uv run ruff format --check` + `ruff check` clean on both touched files (standing
COM812 formatter-conflict notice only). Owned `sets.py` hunk = pass-1 verified form_key
collapse (already closed sibling); only new = the test. No rejection trigger.
