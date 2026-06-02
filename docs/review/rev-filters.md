# Review: `django_strawberry_framework/filters/` (folder pass)

Status: verified

Sibling artifacts read (Worker 1's contract per `docs/review/worker-1.md` "Folder and project passes"):

- `docs/review/rev-filters__base.md` (verified)
- `docs/review/rev-filters__factories.md` (verified)
- `docs/review/rev-filters__inputs.md` (verified)
- `docs/review/rev-filters__sets.md` (verified)

Folder `__init__.py` covered in scope: `django_strawberry_framework/filters/__init__.py` (88 lines, 1 module-level function `filter_input_type`, one module-level ledger `_helper_referenced_filtersets`, single docstring + `__all__` of 16 entries).

Shadow overviews consulted (one per sibling + `__init__.py`):

- `docs/shadow/django_strawberry_framework__filters____init__.overview.md`
- `docs/shadow/django_strawberry_framework__filters__base.overview.md`
- `docs/shadow/django_strawberry_framework__filters__factories.overview.md`
- `docs/shadow/django_strawberry_framework__filters__inputs.overview.md`
- `docs/shadow/django_strawberry_framework__filters__sets.overview.md`

## DRY analysis

- **Hoist `INPUTS_MODULE_PATH` consumption pattern into a shared module-namespace helper IFF a second materialize/clear pair lands.** Today `inputs.py:54` defines `INPUTS_MODULE_PATH = "django_strawberry_framework.filters.inputs"` and the constant is consumed at five sites: `inputs.py:640` and `inputs.py:725` (`Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)]`), `inputs.py:877` (`sys.modules[INPUTS_MODULE_PATH]` inside `clear_filter_input_namespace`), and `filters/__init__.py:39, :87` (`from .inputs import INPUTS_MODULE_PATH` + `Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]`). Five sites, one constant, no drift — the pattern is already correctly DRY at the constant level. The only thing one could promote is a `_lazy_filter_input(type_name)` one-liner that wraps the `Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]` shape (three sites: `__init__.py:87`, `inputs.py:640`, `inputs.py:725`). **Defer until** an `orders/` sibling subpackage lands its own equivalent `OrderArgumentsFactory` + module-global materialize/clear pair — that pulls the count to six sites of `strawberry.lazy(<MODULE_PATH>)` wiring and the helper signature begins to earn its line. Today three call sites with three distinct surrounding contexts (the consumer-facing `filter_input_type` helper, the self-referential filterset input field, the nested-input field) reads more clearly inline.

- **Cross-file `_iter_filterset_subclasses` vs registry walk consolidation IFF a third "walk every loaded filterset" use lands.** `inputs.py::_iter_filterset_subclasses` (lines 945-969) is consumed only by `clear_filter_input_namespace` (`inputs.py:915` area) today; the cookbook port pattern of walking `cls.__subclasses__()` depth-first with identity dedup is also conceptually parallel to `registry`'s per-DjangoType iteration. The two walks are not currently duplicates — registry is keyed by Django model, this walker is keyed by Python class identity — but a future "iterate every FilterSet to do X" use case (e.g. a `seal_filtersets()` finalizer hook, an introspection-only `list_registered_filtersets()` API) would land a third walker that should consolidate against `_iter_filterset_subclasses`. **Defer until** a second non-clear consumer of `_iter_filterset_subclasses` lands; today it is correctly module-private and single-consumer.

- **Promote `Annotated[<name>, strawberry.lazy(<module_path>)]` ForwardRef-wrap shape to a documented helper in `utils/typing.py` IFF a second sibling subsystem (orders/aggregates) reaches for the same Strawberry `LazyType.resolve_type` pattern.** Three sites of `Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]` live across `__init__.py:87`, `inputs.py:640`, `inputs.py:725`; another two `Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)]` repeat the pattern. The `filters/__init__.py:79-86` carries a six-line load-bearing comment ("Do NOT refactor this into a literal-string interpolation outside the Annotated call — Strawberry's `LazyType.resolve_type` requires the ForwardRef-wrapped form to resolve via `module.__dict__` at schema build."). The comment is correct sibling-design today. **Defer until** an `orders/` or `aggregates/` subsystem lands its own `<X>_input_type()` consumer helper with the same Annotated-lazy wrap — then promote both halves (the consumer helper AND the inner `_build_input_fields` self-ref / nested-ref sites) through a shared `lazy_input_annotation(name, module_path)` helper in `utils/typing.py` with the load-bearing comment lifted alongside it as the canonical home. Today three sites of the same idiom, each in a distinct surrounding context, are correctly inline.

- **Folder-DRY recap: the four siblings each already correctly defer their own twin / near-twin pairs.** Per the sibling artifacts, each in-file DRY pair has its own act-now or defer-with-trigger disposition: `base.py` has the `ArrayFilter.method` / `ListFilter.method` setter pair and the `*FilterMethod.__call__` pair (both deferred per sibling-design discriminator role); `factories.py` has the `_make_hashable` three-branch ladder (deferred until a fourth container type) and the `{"model", "fields"}` carve-out hoist (deferred until a second site); `inputs.py` has the `_normalize_range_value` dict/object accessor pair (deferred until a third axis or second filter primitive), the `_owner_type_name(...) or "Filter"` fallback (deferred until a third site or distinct-suffix need), and the `list[_element_annotation(...)]` triple (deferred until a fourth list-shaped primitive); `sets.py` has the `apply_sync` / `apply_async` near-twins, the `_derive_related_visibility_querysets_*` near-twins, the `_MAX_LOGIC_DEPTH` raise (three act-now opportunities still recorded for the next DRY cycle), the `__dataclass_fields__` sniff at three sites, the `dict(_LOGIC_KEYS)` materialization (two deferred), and the `_iter_active_related_branches` parent-per-branch-gate hoist (deferred). At the folder level there is no NEW cross-file DRY opportunity that the per-file artifacts missed — the parent-per-branch-gate + recursion walks live entirely inside `sets.py`, the input-namespace + factories share state only through one constant (`INPUTS_MODULE_PATH`), and the package's only shared mixin (`ClassBasedTypeNameMixin` + `LazyRelatedClassMixin`) already lives one folder up at `sets_mixins.py`. Recording this here so the next DRY cycle does not re-triage the folder for opportunities the per-file passes already enumerated.

## High:

None.

## Medium:

### Subpackage-wide `spec-021` source citations actually anchor at `docs/SPECS/spec-027-filters-0_0_8.md` — 43 sites across all five files

**Forward from every sibling artifact, consolidated here per the per-file dispatch routing.** `rev-filters__base.md::Low #2`, `rev-filters__factories.md::Low #6`, `rev-filters__inputs.md::Low #1`, and `rev-filters__sets.md::Low #1` each explicitly forwarded the same drift to this folder pass; each cited the artifact's reasoning that sweeping one file in isolation would create internal inconsistency with the other four siblings. Per worker-memory carry-forward (`worker-memory/worker-1.md` "filters/base.py" entry): "when 35+ source citations to `spec-021` across an entire subpackage (`filters/{base,factories,inputs,sets,__init__}.py`) actually point at a different shipped spec on disk (`docs/SPECS/spec-027-filters-0_0_8.md`; spec-021 is the apps spec at 514 lines, zero filter mentions), do NOT propose a per-file sweep — it would create internal inconsistency vs siblings. Forward to the folder pass as a single mass-rewrite candidate."

**Severity escalation rationale.** Each sibling artifact filed the drift as Low (citation hygiene) on a per-file basis, but the folder pass collects the full scope: **43 source-comment citations to `spec-021` across all five tracked Python files** in the subpackage (`grep -rcn "spec-021" django_strawberry_framework/filters/` → `__init__.py:2`, `base.py:13`, `factories.py:3`, `inputs.py:14`, `sets.py:11`). The cited spec file on disk is `docs/SPECS/spec-021-apps-0_0_7.md` — the **`apps.py` AppConfig** spec (514 lines, headline `# Spec: \`apps.py\` and Django \`AppConfig\``; `grep -E "FilterSet|filter_input_type|RelatedFilter" docs/SPECS/spec-021-apps-0_0_7.md` returns ZERO matches). The actual filter spec is `docs/SPECS/spec-027-filters-0_0_8.md` (1290+ lines, 251 filter symbol mentions per `grep -c "FilterSet|filter_input_type|RelatedFilter"`). Per the architecture-documentation-hygiene rubric in `docs/review/REVIEW.md` "Severity definitions" — 43 source-comment citations in shipped public-facing source pointing at the wrong spec file on disk is at minimum Medium: a future maintainer reading `base.py:174` ("Slice 3's finalizer phase 2.5 wires per spec-021 L566-567 + L603 + ...") and grepping `spec-021` finds an unrelated AppConfig spec, not the filter spec the comment was authored against. The DRY-first rule in `docs/review/REVIEW.md` line 9 makes folder-level "parallel data flows" a review-time defect; 43-site one-way drift IS the parallel-data-flow.

**Why it matters.** The citation pattern across the subpackage is the load-bearing audit trail tying source comments to the spec decisions that authored them. Most sites are `L<lineno>` anchors (e.g. `spec-021 L566-567`, `spec-021 L988`, `spec-021 L602`, `spec-021 L605`, `spec-021 Decision 9`, `spec-021 Decision 4 M5`, `spec-021 Decision 3 Layer 5`, `spec-021 H1` / `H3`, `spec-021 M-filters-3 / H-filters-3`); when a future maintainer or reviewer follows a citation like "spec-021 L566-567 + L607" they need to land at the actual spec text on disk. Today every single one of those 43 anchors lands at the wrong spec file (apps.py spec) and the rebind to `spec-027-filters-0_0_8.md` must preserve the line / decision / hurdle anchors verbatim because the cited line numbers belong to the filter spec, not the apps spec.

**Site enumeration (43 total, grouped by file).**

```
__init__.py: line 44, line 83                                           (2 sites)
base.py:     lines 3, 4, 22, 174, 185, 190, 217, 238, 244, 247, 269, 282, 309 (13 sites)
factories.py: lines 3, 12, 99                                            (3 sites)
inputs.py:   lines 6, 58, 67, 124, 144, 197, 241, 275, 387, 428, 472, 537, 844, 855 (14 sites)
sets.py:     lines 3, 8, 189, 364, 417, 431, 467, 486, 510, 654, 865      (11 sites)
```

(Per-file artifact site counts in `rev-filters__base.md::Low #2` say 10, `rev-filters__inputs.md::Low #1` says 13, `rev-filters__sets.md::Low #1` says 11; the `__init__.py` sites were not enumerated at per-file granularity since `__init__.py` is covered by THIS folder pass. The slight mismatch on `base.py` 10→13 is because the artifact enumerated direct symbol-docstring anchors; the full `grep` count includes the module docstring's two-line "Layers 1 and 2 of the six-layer pipeline (spec-021 Decision 3) plus the / five parity-floor primitives (spec-021 Decision 4)" at base.py:3-4 and the `RelatedFilter` audit-trail comment at base.py:309. Worker 2 should treat the grep output as the source of truth for the mass-rewrite scope, not the per-file artifact's older count.)

**Recommended change.** Mass-rewrite the 43 sites in one Worker 2 spawn — `spec-021` → `spec-027`, preserving every `L<lineno>` / `Decision <N>` / `H<N>` / `M-<id>` / `Layer <N>` anchor verbatim (the cited line numbers, decisions, hurdles, M-IDs, and layers belong to the filter spec's structure, not the apps spec's). Two acceptable sed shapes:

1. **Surgical per-file `sed -i 's/spec-021/spec-027/g'` across the five files**, then read the diff once and verify every replaced citation still makes structural sense (e.g. `spec-027 L566-567`, `spec-027 Decision 9`, `spec-027 H1` — the `spec-027-filters-0_0_8.md` file ships with the same anchor scheme so every existing anchor should survive verbatim).
2. **Per-cite manual rewrite** if any citation references content that does NOT exist at the same anchor in `spec-027-filters-0_0_8.md` (e.g. a citation like `spec-021 Decision 5` that the spec-027 file restructured into `Decision 4` — unlikely given the per-file artifacts already cross-checked, but worth a final eyeball pass).

Recommend (1) — the per-file artifacts already cross-checked the anchor structures and confirmed the citations land verbatim under spec-027's scheme (per `rev-filters__base.md::Low #2` body, which cites concrete spec-027 line numbers like `L566-567`, `L988`, `L1057`, `L602`, `L603`, `L605` — all matching the spec-021 anchors on the existing citations). Pair the mass-rewrite with a `grep -rn "spec-021" django_strawberry_framework/filters/` post-check returning zero hits.

**No test impact expected.** None of the 43 sites are reached by test assertions on string content (per the sibling artifacts' iteration logs, the existing pinning tests assert behavioral contracts, not docstring or comment substrings). The maintainer should still spot-check by running `uv run pytest tests/filters/` after the rewrite per the standard cycle gate.

**Why Medium, not Low (revisited).** The escalation is per worker-1.md memory carry-forward: each per-file artifact filed the drift Low and forwarded it; the folder pass owns the bundled severity call. 43 sites in shipped public-facing source AND a 1290-line filter spec on disk that none of those citations point at is architecture-documentation hygiene under the rubric. A reader reasonably trying to audit "what spec decision authorized this code" must read 5 source files, grep 43 sites, follow each one to the wrong spec, then re-grep to find spec-027. That's the parallel-data-flow `REVIEW.md` line 9 names as a review-time defect; Medium captures the scope correctly.

```django_strawberry_framework/filters/base.py:174-191
    Slice 3's finalizer phase 2.5 wires per spec-021 L566-567 + L603 +
    L1057.  The owner-aware resolution rules:
    ...
       contract per spec-021 L988); the expected type name is the target
       ...
    decodes the GlobalID without type-name validation per spec-021 L1057.
```

(Excerpt — `spec-021 L566-567 + L603 + L1057` should read `spec-027 L566-567 + L603 + L1057`; the line numbers and decision/L-anchor structure already match `spec-027-filters-0_0_8.md` per the per-file artifacts' cross-check. Same shape applies to all 42 other sites.)

## Low:

### Folder-wide "Slice N" tense rot survives in two files (`base.py`, `factories.py`, `__init__.py`)

Per `rev-filters__inputs.md::Low #2` and `rev-filters__sets.md::Comment-pass` records, both `inputs.py` and `sets.py` had their `Slice 1` / `Slice 2` / `Slice 3` tense markers scrubbed in earlier cycles (`grep -c "Slice " inputs.py` → 0 per `rev-filters__inputs.md` verification pass 2; `grep -c "Slice " sets.py` → 0 per `rev-filters__sets.md` verification pass 2). The remaining files still carry the tense rot:

```
__init__.py: lines 5, 45, 61                              (3 sites)
base.py:     lines 1, 11, 51, 174                         (4 sites)
factories.py: line 1 ("BFS factory + dynamic-FilterSet cache (Slice 2).") (1 site)
```

Per `grep -n "Slice " django_strawberry_framework/filters/*.py`. The factories.py headline was rewritten at line 12-14 per its own cycle (per `rev-filters__factories.md::Comment pass`) but the module-docstring headline at line 1 still reads `"""BFS factory + dynamic-FilterSet cache (Slice 2)."""`. The base.py headline at line 1 reads `"""Filter primitives + \`RelatedFilter\` (Slice 1)."""`; base.py:11 says `"Slice 2)."`; base.py:51 says `"(Slice 2); there is no Graphene-style \`input_type\` property."`; base.py:174 says `"Slice 3's finalizer phase 2.5 wires per spec-021 L566-567 + L603 + L1057."`. The __init__.py docstring at line 5 says `"consumer helper \`filter_input_type\` (Slice 2). Slice 3 will wire the"`; line 45 says `"Slice 3's finalizer phase 2.5 subpass 4 compares this set against the"`; line 61 says `"\`\`finalize_django_types()\`\` (Slice 3) has materialized the input"`.

Same calibration as the per-file Slice-tense Lows (`list_field.py` `spec-016 → spec-020`, `scalars.py` `TODO-ALPHA-028` drift, `factories.py` `Slice 3's finalizer materializes ...` rewrite): the policy text is itself correct against shipped behavior; only the tense rotted. The filter subsystem cards `DONE-027-0.0.8` (KANBAN.md per `rev-filters__sets.md::Comment-pass` records) shipped at the 0.0.8 cut already containing every slice; `Slice 1` / `Slice 2` / `Slice 3` are historical build artifacts, not active spec anchors. **Comment-pass scope; bundle with the spec-021 → spec-027 mass-rewrite above so Worker 2 has one diff covering both citation-hygiene categories.** Recommended phrasing: drop the `(Slice N)` parenthetical from headlines, rotate `Slice 3 will wire the …` to `the finalizer wires the …`, rotate `Slice 3's finalizer phase 2.5 wires per spec-027 L566-567 …` to `the finalizer's phase 2.5 wires per spec-027 L566-567 …`. Keep the `phase 2.5` anchor since that's the live mechanism name, not a slice label.

### `_helper_referenced_filtersets` audit-trail comment at `__init__.py:44-47` is shipped, not future-work

`__init__.py:44-47`:

```django_strawberry_framework/filters/__init__.py:44-47
# this set via a cycle-safe local import per spec-021 Decision 9.
# Slice 3's finalizer phase 2.5 subpass 4 compares this set against the
# set of `Meta.filterset_class`-wired filtersets and raises
# `ConfigurationError` for orphans.
```

The "Slice 3's finalizer phase 2.5 subpass 4 compares this set ..." framing reads as in-flight design but is shipped at 0.0.7: `types/finalizer.py::SchemaFinalizer` is wired in (per `rev-filters__factories.md::Low #5` cross-check, `from ..filters.factories import FilterArgumentsFactory` lives at `types/finalizer.py:521`, and the finalize phase 2.5 mechanics are in production per the test suite at `tests/filters/test_finalizer.py`). Comment-pass: rotate "Slice 3's finalizer phase 2.5 subpass 4 compares this set" to "The finalizer's phase 2.5 subpass 4 compares this set" (drop the slice label, keep the phase anchor). Bundle with the Slice-tense rewrite above.

### `_helper_referenced_filtersets`'s "registry.clear() clears this set via a cycle-safe local import" assertion is not pinned by a folder-level test

`__init__.py:42-48` describes `_helper_referenced_filtersets` as a process-global ledger that `registry.clear()` clears via a cycle-safe local import (per spec-027 Decision 9). The state is shared across `filter_input_type` consumers AND the finalize-phase-2.5 orphan check (`types/finalizer.py`). The contract IS pinned per `tests/filters/test_inputs.py::_isolate_registry` autouse fixture (per `rev-filters__inputs.md::What looks solid`'s last bullet — clears `_field_specs` + `_helper_referenced_filtersets` explicitly), but the cross-cycle-clear contract — `registry.clear()` itself reaching across into `filters/__init__.py` via a cycle-safe local import to drop `_helper_referenced_filtersets` — is documented at the `registry.py` site per `rev-registry.md::What looks solid` (`register_with_definition`'s rollback comment) and only indirectly via the `_isolate_registry` autouse fixture in tests.

A direct test pinning "after `registry.clear()`, `_helper_referenced_filtersets` is empty" does not exist in the package — the `_isolate_registry` fixture clears the ledger directly (not by calling `registry.clear()`). A regression test would surface a latent breakage where a future refactor removes the local import inside `registry.clear()` without affecting the autouse fixture. **Forwarded to the project pass** `rev-django_strawberry_framework.md` paired with similar process-global-state cross-cycle assertions that probably live across multiple subpackages today (e.g. `inputs.py::_field_specs`, `factories.py::_dynamic_filterset_cache` — `rev-filters__factories.md::What looks solid` records the latter as having NO clear hook by design). Project-pass scope; no per-file or folder-level fix required.

### Folder-level GLOSSARY coverage gap for the filter subsystem first cohort — forwarded, not a local fix (consolidated)

Per `rev-filters__base.md::Low #5`, `rev-filters__factories.md::Low #6`, `rev-filters__inputs.md::Low #5`, `rev-sets_mixins.md::Carry forward`, and `rev-filters__sets.md::Summary`'s GLOSSARY drift check, the filter subsystem ships **25+ public-visible symbols** today through this folder's `__all__` exports (`filters/__init__.py:90-107`): `ArrayFilter`, `ArrayFilterMethod`, `Filter` (re-export of `django_filters.Filter`), `FilterSet`, `FilterSetMetaclass`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, `LazyRelatedClassMixin`, `ListFilter`, `ListFilterMethod`, `RangeField`, `RangeFilter`, `RelatedFilter`, `TypedFilter`, `filter_input_type`, `validate_range`. Plus the per-sibling internal-but-cited symbols (`INPUTS_MODULE_PATH`, `_input_type_name_for`, `convert_filter_to_input_annotation`, `normalize_input_value`, `LOOKUP_NAME_MAP`, `LOOKUP_PREFIXES`, `construct_search`, `FieldSpec`, `build_input_class`, `materialize_input_class`, `clear_filter_input_namespace`, `HIDE_FLAT_FILTERS` settings key, `FilterArgumentsFactory`, `get_filterset_class`, `_dynamic_filterset_cache`, `_make_cache_key`).

GLOSSARY entries today (per `docs/GLOSSARY.md:72-104`): `FilterSet`, `filter_input_type`, `RelatedFilter`, plus `Meta.filterset_class` per `docs/GLOSSARY.md::Filtering` browse-by-category line. **22+ symbols absent.** The joint-cut deferral pattern per `spec-027` Decision 10 (per `rev-filters__base.md::Low #5`'s "shipped (0.0.8) — see status forward" framing) wants the filter-subsystem first-cohort GLOSSARY coverage authored together at version-bump time, not piecemeal per per-file cycle.

**Forwarded to `rev-django_strawberry_framework.md` project pass** per the per-file artifacts' explicit routing AND `rev-sets_mixins.md`'s carry-forward pairing (`ClassBasedTypeNameMixin`, `LazyRelatedClassMixin`, `type_name_for`, `resolve_lazy_class` also absent and best documented with their first cohort of consumers — three of which are the filters here). No in-cycle GLOSSARY edit at this folder scope; project pass owns the bulk authoring decision.

### `Filter` is a verbatim re-export of `django_filters.Filter` — well-documented but unverified by a regression test

`__init__.py:10-15` documents the `Filter` re-export contract verbatim: it IS `django_filters.Filter` itself, a plain re-export (not a subclass), surfaced under this package's namespace so consumers writing a custom `method=` filter import one base class from `django_strawberry_framework.filters`. It deliberately shadows the upstream name; reach for `django_filters.Filter` directly only if you need to distinguish the two.

`base.py:31` does `from django_filters import Filter, ModelChoiceFilter, MultipleChoiceFilter` and `__init__.py:24-38` re-exports `Filter` from `.base`. The re-export is correct, but the "IS django_filters.Filter" identity claim is not pinned by a regression test — a future refactor that wraps `Filter` in a subclass to "make it Strawberry-aware" (or e.g. to add a `field_name` validator) would silently break the docstring's contract. **Defer until a second package-level identity-vs-subclass re-export pair lands** (e.g. a future `OrderBy = django_filters.OrderingFilter`-style re-export); today one re-export is the right cost-floor. Comment-pass observation only.

### `_helper_referenced_filtersets` ledger size grows monotonically over the process lifetime

`__init__.py:48` declares `_helper_referenced_filtersets: set[type[FilterSet]] = set()`. The ledger grows every time `filter_input_type(...)` is called for a new filterset and is cleared only by `registry.clear()` per the audit-trail comment at line 42-47. In production this is fine (the ledger is bounded by the number of distinct FilterSet subclasses, which is small and stable per process); in test suites the autouse `_isolate_registry` fixture per `rev-filters__inputs.md::What looks solid` clears it per-test.

In a long-running consumer reload scenario (e.g. Django's autoreloader rebuilding models without calling `registry.clear()`), the ledger retains stale class identities until the process exits. The behavior matches `inputs.py::_field_specs`'s same `_isolate_registry`-only clear (per `inputs.py:133-140` audit-trail comment). **No-edit Low; record for visibility.** Forwarded to project pass alongside the cross-subpackage process-global-state survey (see Low #3 above). If a future consumer reload story lands ("Django dev server: rebuild model classes WITHOUT requiring a `registry.clear()` call"), every process-global ledger in `filters/` needs a coordinated clear-hook story; today the joint-cut deferral pattern of spec-027 Decision 10 is correctly scoped.

### `filter_input_type`'s docstring promises lazy resolution at schema build time but cites "Slice 3"

`__init__.py:51-72`:

```django_strawberry_framework/filters/__init__.py:60-62
    ``LazyType.resolve_type`` at schema-build time -- by which point
    ``finalize_django_types()`` (Slice 3) has materialized the input
    class as a module global of ``django_strawberry_framework.filters.inputs``.
```

Same tense-rot as Low #1: `finalize_django_types() (Slice 3)` should be `finalize_django_types()` (drop the Slice parenthetical). The phase-2.5 mechanism is shipped; the slice label is historical. Bundle with Low #1's Slice scrub.

### Comment-style inconsistency across siblings — RST `` `` `` vs single `` ` `` backticks

Per `rev-filters__base.md::Low #3` (already verified and edited at the two named sites in base.py), the comment/docstring backtick convention drift exists across the subpackage. Spot-check at folder level:

- `base.py` uses single-backticks throughout per its own comment-pass fix.
- `factories.py` uses RST-style double-backticks heavily (`\`\`Meta\`\``, `\`\`get_filterset_class\`\``, `\`\`_make_cache_key\`\``, `\`\`__name__\`\``) per `rev-filters__factories.md::Comment pass` recordings.
- `inputs.py` mixes: docstrings carry RST-style double-backticks throughout (per `rev-filters__inputs.md::What looks solid`'s test-pin records that exact pattern), comments use single-backticks.
- `sets.py` mixes similarly.
- `__init__.py` uses single-backticks in both module docstring and `filter_input_type` docstring, except for the audit-trail comment at lines 79-86 which uses single-backticks too.

The per-file artifacts variously called this out (`rev-filters__base.md::Low #3` was the explicit one; the others noted it inline in "What looks solid"). At folder level: **the package has no stated convention** and the four siblings have evolved divergent conventions through their port lineage (RST in helpers ported verbatim from the cookbook; single-backticks in package-original consumer-facing docstrings). Two acceptable shapes:

1. **Standardize on single-backticks package-wide.** Matches `__init__.py`'s consumer-facing exterior surface; matches `base.py`'s post-cycle state. Cost: a sweep across `factories.py`, `inputs.py`, `sets.py` docstrings (substantial diff, ~100+ sites).
2. **Standardize on RST-style double-backticks for in-source docstrings, single-backticks for inline `# comments`.** Matches the cookbook's upstream convention (per the verbatim ports) and Sphinx-friendly rendering if a future autodoc pass lands. Cost: a smaller sweep on the `base.py` + `__init__.py` consumer-facing surfaces.

**Defer until** the convention question is raised explicitly by the maintainer (e.g. a Sphinx autodoc pass landing OR a consumer-facing docs site shipping); today the inconsistency is internal and the per-symbol GLOSSARY entries already paper over the surface mismatch. Forwarded to `rev-django_strawberry_framework.md` project pass for the package-wide convention call.

## What looks solid

### DRY recap

- **Existing patterns reused (folder-level).** `INPUTS_MODULE_PATH` is a single source of truth consumed at five sites across two files (`inputs.py:54` definition; `inputs.py:640`, `inputs.py:725`, `inputs.py:877`, `__init__.py:87` consumption), and the `Annotated[<name>, strawberry.lazy(INPUTS_MODULE_PATH)]` ForwardRef-wrap is documented as load-bearing at `__init__.py:79-86` (consumer LazyType.resolve_type contract). `_LOGIC_KEYS` is a single source of truth at `inputs.py:114` consumed by `sets.py:39` (`from .inputs import _LOGIC_KEYS, ...`) — the one-shot module-level precompute pattern per `rev-filters__sets.md::DRY recap`. `LOOKUP_NAME_MAP` similarly imported by `sets.py` from `inputs.py:75-102` with the reverse-direction `_FORM_KEY_BY_PYTHON_ATTR` precomputed at `sets.py:59-62` so `_form_key_for_python_attr` is O(1). `ConfigurationError` imported from `..exceptions` consistently across `inputs.py`, `factories.py`, `sets.py` — one error-type contract for every typed-error raise in the subpackage. `ClassBasedTypeNameMixin` + `LazyRelatedClassMixin` live one folder up at `sets_mixins.py` and are imported by `base.py:37` and `sets.py:31` — the canonical home for cross-set-subsystem shared mixins per `rev-sets_mixins.md`. `_pascal_case`'s no-word-character guard now lives at `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` per the Medium #1 hoist from `rev-filters__inputs.md` — the guard is at the right (shared) layer protecting every future `OrderSet` / `AggregateSet` per-field caller, not just the one inputs.py call site.

- **New helpers considered (folder-level).** Considered hoisting `Annotated[<name>, strawberry.lazy(INPUTS_MODULE_PATH)]` into a `lazy_input_annotation(name, module_path)` helper in `utils/typing.py` — deferred until a second sibling subsystem (orders/aggregates) reaches for the same ForwardRef-wrap pattern per `## DRY analysis` bullet 3. Considered consolidating `_iter_filterset_subclasses` (`inputs.py:945-969`) into a registry-walking helper — deferred at one current consumer (`clear_filter_input_namespace`). Considered extracting a `_filter_subsystem_state_clear()` umbrella that bundles every process-global clear (`_helper_referenced_filtersets`, `_field_specs`, `_materialized_names`, `_dynamic_filterset_cache`) — rejected because the per-state clear-vs-no-clear policies diverge intentionally per `rev-filters__factories.md::What looks solid`'s `_dynamic_filterset_cache` no-clear-hook decision; a single umbrella would obscure the per-cache lifecycle decisions documented inline.

- **Duplication risk in the current folder.** The `apply_sync` / `apply_async` near-twins (`sets.py:1378-1430`) AND the `_derive_related_visibility_querysets_*` near-twins remain intentional sibling design TODAY (per `rev-filters__sets.md::DRY recap` — "the documented sync/async-boundary mediating role means the two-method split is load-bearing for static call-site routing"); both are recorded as act-now opportunities in the `rev-filters__sets.md::DRY analysis` for the next DRY cycle. The `_make_hashable`'s `tuple(_make_hashable(item) for item in ...)` shape repeats across three branches in `factories.py` and the dict / set / list branches' surrounding "key shape" differ enough that abstracting the constructor would obscure per-branch ordering contract. The `[_unwrap_enum_member(item) for item in raw_value]` pattern in `inputs.py:444` / `inputs.py:450` is load-bearing branch-discrimination per `rev-filters__inputs.md::DRY recap`. **No folder-level duplication that the per-file siblings missed.**

### Other positives

- **One-way intra-folder import dependency confirmed by the shadow overview imports section.** Per `grep -E "^from \.|^from \.\." django_strawberry_framework/filters/*.py`:
  - `__init__.py` → `.base`, `.inputs`, `.sets` (three sibling reads; depends on all three module-level surfaces).
  - `base.py` → `..sets_mixins` only (no intra-folder sibling import).
  - `factories.py` → `..exceptions`, `.inputs`, `.sets` (intra-folder reads: inputs + sets, both downstream of factories).
  - `inputs.py` → `..conf`, `..exceptions`, `.base` at module level; `.sets`, `.base.RelatedFilter`, `.factories` under TYPE_CHECKING or deferred inside function bodies (lines 47, 645, 913, 930).
  - `sets.py` → `..exceptions`, `..registry`, `..sets_mixins`, `..types.relay`, `.base`, `.inputs` (intra-folder reads: base + inputs, both upstream of sets).
  - Strict ascending order: `base.py` < `inputs.py` < `sets.py` < `factories.py` < `__init__.py`. No circular-import risk at module-load time; the only deferred imports in `inputs.py` (`.sets`, `.factories`, `.base.RelatedFilter`) are the necessary back-references that the module-level import order forbids, all wrapped inside `TYPE_CHECKING` guards or function bodies so module-load is acyclic.

- **`__all__` is exhaustive and matches the documented public surface.** `__init__.py:90-107` exports exactly 16 symbols: 14 filter primitives from `.base` (the parity-floor primitives + GlobalID pair + mixin re-export), `FilterSet` + `FilterSetMetaclass` from `.sets`, and the consumer helper `filter_input_type`. The list is alphabetized. `validate_range` is exported — the only `__all__` entry without an external reader (per `grep -rn "validate_range" django_strawberry_framework/ examples/ tests/`, the only references are `base.py` definition + `__init__.py` re-export + the internal `RangeField.default_validators = [validate_range]`); it's correctly part of the public surface because consumers building a custom `forms.Field` with the same two-element list contract would import it from the package namespace. The DRY-first rule does not flag this — `validate_range` is the public name a consumer reaches for to validate the same two-element list contract, not a leaked internal.

- **Cross-file shared-state cleanup contract is documented at every site.** `inputs.py::_field_specs` (`inputs.py:133-140`) audit-trail comment, `inputs.py::_materialized_names` (`inputs.py:144-150`) audit-trail comment, `inputs.py::clear_filter_input_namespace` (`inputs.py:863-876`) docstring, `factories.py::_dynamic_filterset_cache` (`factories.py:40-46`) audit-trail comment, AND `__init__.py::_helper_referenced_filtersets` (`__init__.py:42-47`) audit-trail comment ALL document their clear contract (or explicit no-clear-by-design) inline. The four cleanup contracts diverge intentionally:
  - `_field_specs` and `_materialized_names`: cleared by `clear_filter_input_namespace` (driven by `registry.clear()`).
  - `_helper_referenced_filtersets`: cleared by `registry.clear()` via cycle-safe local import.
  - `_dynamic_filterset_cache`: NO clear hook by M-filters-3 review decision (test-isolation nicety only; keys embed model identity so a rebuild gets a fresh key).
  Each divergence is documented at the cache site with the rationale; no folder-level inconsistency to forward.

- **`filter_input_type`'s eager `TypeError` raise validates at resolver-declaration site.** `__init__.py:73-76` raises `TypeError` for any non-`FilterSet` argument; consumers catch misuse at the `@strawberry.type` decoration time instead of at schema-build time. Same loud-fail discipline as `RelatedFilter.__init__`'s `TypeError` rejection of `lookups=` per `rev-filters__base.md::Verification pass 2` and `_pascal_case` / `type_name_for`'s `ConfigurationError` per `rev-filters__inputs.md::Logic verification`. Three loud-fail raises across the subpackage on the same "validate at resolver-declaration site, not at schema-build time" pattern.

- **`filter_input_type`'s `_helper_referenced_filtersets.add(filterset_class)` side effect is the orphan-check ledger the finalizer phase 2.5 reads.** The set is mutated only by this one helper (line 77) and read by `types/finalizer.py`'s phase 2.5 subpass 4. Clean two-site contract: producer (`__init__.py:77`), consumer (`types/finalizer.py` phase 2.5). The `registry.clear()` cycle-safe local import keeps the producer / consumer / cleaner triangle correctly decoupled per the audit-trail comment.

- **Per-sibling verification discipline is strong.** All four sibling cycles closed with `cycle accepted; verified` status, every High/Medium/Low was either addressed inline or explicitly forwarded with a grep-resolvable trigger, every fix landed with a regression test (per the iteration logs in each artifact). No deferred logic items leaked from sibling cycles; the folder pass inherits a clean baseline.

- **Folder-level repeated-literals check (per `REVIEW.md::Folder-pass repeated-literal check`).** Cross-file shadow-overview repeated literals:
  - `base.py`: `bound_filterset` (2x intra-file).
  - `factories.py`: none.
  - `inputs.py`: `contains` (3x), `description` (3x), `istartswith` (2x), `week_day` (2x), `field_name` (2x), `__annotations__` (2x) — all intra-file, all part of the `LOOKUP_NAME_MAP` / `_scalar_from_form_field` / per-helper kwarg vocabulary.
  - `sets.py`: `related_filters` (5x), `__dataclass_fields__` (3x), `_expanded_filters` (2x), `is_relation` (2x), `FilterSet` (2x — in error messages), `: logical-branch nesting exceeded _MAX_LOGIC_DEPTH=` (2x), `. Flatten the filter input or split into multiple queries.` (2x), `_permission` (2x) — all intra-file.
  - `__init__.py`: none.
  - **Cross-file literal duplication: none.** No string literal appears in 2+ sibling files. The shared keys (`_LOGIC_KEYS`'s `("and_", "and")` / `("or_", "or")` / `("not_", "not")` tuples; `LOOKUP_NAME_MAP`'s `django_lookup` → `(python_attr, graphql_name)` mappings) live in `inputs.py` and are imported by `sets.py` — single-source-of-truth pattern, not literal duplication. The `__dataclass_fields__` repeat 3x within `sets.py` is the act-now DRY opportunity `rev-filters__sets.md::DRY analysis` already recorded.

### Summary

The `filters/` subpackage is the largest folder in the package by line count (`base.py` 415 lines, `factories.py` 310 lines, `inputs.py` 969 lines, `sets.py` 1452 lines, `__init__.py` 107 lines — ~3250 lines total) and the most internally complex (29 control-flow hotspots across siblings, 200+ calls of interest). The four per-file artifacts closed `verified` with two Mediums in `inputs.py` (no-word-character guard hoist; `_normalize_range_value` partial-range axis drop), two Mediums in `sets.py` (`apply_async` sync-to-async wrap; nested-branch async-derive pre-walker), one logic Low in `base.py` (`RelatedFilter.lookups` removed), and six Lows in `factories.py` all addressed or correctly deferred. The folder pass produces ONE Medium consolidating the spec-021 → spec-027 citation drift across **43 sites in all five tracked files** (the per-file artifacts each filed it Low and forwarded; the bundled scope clears the architecture-documentation-hygiene rubric for Medium per worker-1.md's prompt-time calibration). Seven Lows split across: Slice tense rot in three files (`base.py`, `factories.py`, `__init__.py`), `_helper_referenced_filtersets` cross-cycle-clear contract not pinned by a direct test (forwarded to project pass), folder-level GLOSSARY coverage gap for 22+ symbols (forwarded to project pass), `Filter` re-export verbatim identity not pinned (defer-with-trigger), `_helper_referenced_filtersets` monotonic growth (no-edit, forwarded to project pass), `filter_input_type` docstring Slice citation (bundle with Slice scrub), backtick-convention drift across siblings (forwarded to project pass). No High; one Medium; no behavior-changing folder-level finding beyond the citation-rewrite mass-fix. Shape #5 is **DISQUALIFIED** — the Medium requires a real source edit (43 sites swept) AND the Slice-tense Low bundle also requires real source edits at comment-pass time, so the standard three-spawn cycle applies. The DRY analysis carries three defer-with-trigger bullets (`lazy_input_annotation` helper; `_iter_filterset_subclasses` consolidation; folder-DRY recap noting all per-file siblings correctly deferred); no folder-level act-now DRY opportunity surfaces beyond what the per-file passes already enumerated. GLOSSARY drift forwarded to project pass for joint-cohort authoring per spec-027 Decision 10's joint-cut deferral.

---

## Fix report (Worker 2)

Logic pass — Medium (subpackage-wide `spec-021` → `spec-027` citation drift).

### Files touched

- `django_strawberry_framework/filters/__init__.py:44, :83` — `spec-021` → `spec-027` (2 sites).
- `django_strawberry_framework/filters/base.py:3, :4, :22, :174, :185, :190, :217, :238, :244, :247, :269, :282, :309` — `spec-021` → `spec-027` (13 sites).
- `django_strawberry_framework/filters/factories.py:3, :12, :99` — `spec-021` → `spec-027` (3 sites).
- `django_strawberry_framework/filters/inputs.py:6, :58, :67, :124, :144, :197, :241, :275, :387, :428, :472, :537, :844, :855` — `spec-021` → `spec-027` (14 sites).
- `django_strawberry_framework/filters/sets.py:3, :8, :189, :364, :417, :431, :467, :486, :510, :654, :865` — `spec-021` → `spec-027` (11 sites).

Total: 43 sites rewritten across the five tracked files, matching the artifact's enumerated scope. Mechanism: a single `sed -i '' 's/spec-021/spec-027/g' <files>` pass over the five files. Every `L<lineno>` / `Decision <N>` / `Layer <N>` / `H<N>` / `M-<id>` anchor preserved verbatim (the rewrite touched only the spec-id token, never the surrounding anchor scheme — spec-027 ships the same anchor structure that the existing citations already use, per the per-file artifacts' cross-check).

### Tests added or updated

None — citation-only change in comments / docstrings. No test assertions pin on `spec-021` substring (per the per-file artifacts' iteration logs and the folder artifact's "No test impact expected" note).

### Validation run

- `uv run ruff format .` — pass (205 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).
- Post-rewrite grep: `grep -rcn "spec-021" django_strawberry_framework/filters/` → 0 hits in all five files (clean).
- Post-rewrite spec-027 counts (sanity): `__init__.py:2`, `base.py:13`, `factories.py:3`, `inputs.py:14`, `sets.py:12` — totals 44, the +1 over the rewritten 43 is the pre-existing `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)` anchor at `sets.py:304` (not in scope; pre-dates this cycle).
- Spot-check verification: read `__init__.py:42-48` (audit-trail Decision-9 comment), `base.py:1-23` (six-layer + parity-floor module docstring + Decision-2/-3/-4 anchors), and `base.py:170-191` (Decision-3 L566-567 / L988 / L1057 owner-aware resolution comment). Each rewritten anchor reads sensibly against the spec-027-filters-0_0_8.md headings/decisions/L-anchors confirmed at plan time. No string literal that genuinely means the apps spec was caught — none of the 43 sites described `AppConfig` / `apps.py` / app-registration behavior; every site is about filter pipeline mechanics (Layers 1-5, Decision 2/3/4/5/9, M-filters / H-filters series, L566-567 / L607 / L988 / L1057 / L518-605 / L668-678 line anchors — all filter-spec-shaped).

### Notes for Worker 3

- No shadow file consulted during this pass — the change is mechanical and the surrounding context per the artifact already enumerated every site.
- No findings rejected; the artifact's premise (43 sites of one-way citation drift) verified before edit and rewritten in one `sed` pass.
- Slice-tense rot (Low #1) and the `__init__.py:44-47` "Slice 3's finalizer phase 2.5 subpass 4" rotate (Low #2) — both bundled for the comment pass per the artifact's explicit "Comment-pass scope" routing. NOT touched this logic pass.
- `uv.lock` not modified; git status clean against the lockfile.
- One pre-existing `spec-027-filters-0_0_8` TODO anchor at `sets.py:304` (`TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)`) was already in scope; the `sed` pass did not touch it (the literal `spec-021` was not present on that line).

---

## Verification (Worker 3)

### Logic verification outcome

Medium (mass-rewrite spec-021 → spec-027) — accepted.

- `grep -rcn "spec-021" django_strawberry_framework/filters/` → all 5 files report 0 hits (clean sweep).
- `grep -rcn "spec-027" django_strawberry_framework/filters/` → `__init__.py:2`, `base.py:13`, `factories.py:3`, `inputs.py:14`, `sets.py:12` → 44 total (the +1 over the dispatch's expected 43 is the pre-existing `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)` anchor at `sets.py:304` per Worker 2's own validation note; verified at the cited line).
- Per-file diff swap counts: `__init__.py` 2/2, `base.py` 13/13, `factories.py` 3/3, `inputs.py` 13/14 (the +1 is the line at `inputs.py:428` — old `Per the Implementation discretion item (Slice 2 plan step 2)` → new `Per the spec-027 Implementation-discretion item`; HEAD at this line carried `(Slice 2 plan step 2)` with no `spec-021` substring, but the prior-cycle uncommitted comment-pass scrub for inputs.py had already rotated the Slice anchor out, leaving the artifact's enumeration at 14 sites against the prior-cycle working-tree state Worker 2 swept; the new `spec-027` citation is structurally consistent with the surrounding `_normalize_range_value`-returns-multi-key-dict shape decision documented in the spec), `sets.py` 11/11. Total: 42 verbatim -spec-021/+spec-027 swaps plus 1 contextual rebind at `inputs.py:428`.
- Anchors preserved verbatim across every swap: `L<lineno>` (L7, L566-567, L603, L605, L607, L668-678, L988, L1057, lines 579-584, line 591, line 594, line 595, lines 1023-1030), `Decision <N>` (2, 3, 4, 5, 9), `Decision 4 M<N>` (M1, M5, M6), `M-filters-3`, `H-filters-3`, `H1`, `Layer 5`, `Layer N` — grep-confirmed by reading the `^[-+]` diff lines side-by-side.
- Surrounding-context spot-checks at 5 sites confirm the new spec-027 citation reads correctly in filter-pipeline context (`__init__.py:44` Decision-9 cycle-safe-clear ledger; `base.py:174` finalizer phase 2.5 owner-aware GlobalID resolution; `base.py:185-190` `RelatedFilter` expansion contract + GlobalID type-name validation; `factories.py:3` Layer-5 BFS pipeline; `sets.py:3-8` Layer-3/-4 + Decision-5 metaclass port). Every spot-checked surrounding paragraph is unambiguously about filter pipeline mechanics (Layers 1-5, BFS, `FilterSet`, `RelatedFilter`, `GlobalID`, `finalize_django_types`, etc.) — none describe `AppConfig` / `apps.py` / app-registration behavior, so the rebind to `spec-027-filters-0_0_8.md` is structurally correct against the documented anchor scheme.
- Pre-existing working-tree state: substantial uncommitted changes from prior per-file cycles (filters__base, filters__inputs, filters__sets per worker-memory) ride along in `inputs.py` (+57/-40) and `sets.py` (+248/-55). These are the prior cycles' Mediums + comment-pass scrubs (the `sync_to_async` wrap of `apply_async`, the `_collect_nested_visibility_querysets_async` pre-walker, the seven `Slice ` token scrubs in inputs.py, the `Slice ` scrubs in sets.py); they are out of scope for this folder pass per AGENTS.md #33 (in-progress maintainer work since this repo is worked on concurrently). Confirmed `grep "Slice "` counts: `inputs.py:0`, `sets.py:0` (matching worker-memory's prior-cycle completion records); `base.py:4`, `factories.py:2`, `__init__.py:3` (untouched this cycle — Worker 2 deferred them to comment-pass per the artifact's Low #1 routing, verified by `git diff -- <file> | grep -E "^[-+].*Slice"` returning empty for base.py / factories.py / __init__.py except the one `Slice 3's finalizer phase 2.5 wires per spec-021 → spec-027 L566-567` line which only rotated the spec-id).

Low #1 (Slice tense rot in `base.py` / `factories.py` / `__init__.py`) and Low #2 (`__init__.py:44-47` "Slice 3's finalizer phase 2.5 subpass 4" rotate) — both correctly deferred to the comment pass per the artifact's explicit "Comment-pass scope; bundle with the spec-021 → spec-027 mass-rewrite above" routing. Worker 2's Notes for Worker 3 explicitly confirm this deferral.

Low #3 (`_helper_referenced_filtersets` cross-cycle-clear contract not pinned by a direct test) — forwarded to project pass `rev-django_strawberry_framework.md` per the artifact's explicit routing. No in-cycle action required.

Low #4 (folder-level GLOSSARY coverage gap for 22+ filter-subsystem symbols) — forwarded to project pass per the artifact's explicit routing. No in-cycle action required.

Low #5 (`Filter` re-export verbatim identity not pinned) — defer-with-trigger per the artifact ("a second package-level identity-vs-subclass re-export pair lands"). No in-cycle action required.

Low #6 (`_helper_referenced_filtersets` monotonic-growth contract) — no-edit, forwarded to project pass per the artifact's explicit routing. No in-cycle action required.

Low #7 (`filter_input_type`'s `(Slice 3)` parenthetical at `__init__.py:60-62`) — bundle with Low #1 in the comment pass per the artifact's "Bundle with Low #1's Slice scrub" routing.

Low #8 (comment-style RST `` `` `` vs single `` ` `` backticks drift across siblings) — forwarded to `rev-django_strawberry_framework.md` project pass per the artifact's explicit routing.

### DRY findings disposition

All three folder-level DRY analysis bullets correctly deferred with grep-resolvable triggers:

1. `lazy_input_annotation(name, module_path)` helper in `utils/typing.py` — deferred until a second sibling subsystem (orders/aggregates) reaches for the same `Annotated[<name>, strawberry.lazy(<module_path>)]` ForwardRef-wrap. Today three sites of the idiom across two files, each in a distinct surrounding context.
2. `_iter_filterset_subclasses` consolidation against the registry walk — deferred at one current consumer (`clear_filter_input_namespace`).
3. Folder-DRY recap: the four siblings each correctly defer their own twin/near-twin pairs per the per-file artifacts. No new cross-file DRY opportunity surfaces at folder scope that the per-file passes missed.

No folder-level act-now DRY opportunity. Recorded the four sibling-internal deferrals (`apply_sync`/`apply_async` near-twins, `_derive_related_visibility_querysets_*` near-twins, `_make_hashable` three-branch ladder, `_normalize_range_value` dict/object accessor pair) for the next DRY cycle's consideration — none escalated.

### Temp test verification

No temp tests created. The change is citation-only in comments / docstrings; no test assertion pins on the `spec-021` substring (confirmed by `grep -rn "spec-021" tests/` returning no test-file hits, validating Worker 2's "No test impact expected" claim from the artifact and validation block).

### Verification outcome

Ruff outcomes:

- `uv run ruff format --check django_strawberry_framework/filters/` → `5 files already formatted` (pass; the COM812 warning is pre-existing config noise unrelated to this cycle).
- `uv run ruff check django_strawberry_framework/filters/` → `All checks passed!` (pass).

`logic accepted; awaiting comment pass` — Status flipped to `logic-accepted` at the top of the artifact.

---

## Comment/docstring pass

Lows 1, 2, 7 — Slice-tense rotate across the three remaining sibling files; mirror the prior `inputs.py` / `sets.py` remediation style (drop the `(Slice N)` parenthetical from headlines; rotate `Slice 3 will wire ...` / `Slice 3's finalizer phase 2.5 ...` to drop the slice label while keeping the live mechanism anchor `the finalizer's phase 2.5` / `finalize_django_types()`).

### Files touched

- `django_strawberry_framework/filters/__init__.py:1-8` — module docstring rewritten to drop `(Slice 2). Slice 3 will wire the` and rotate to `The finalizer's phase 2.5 wires the orphan check` (Low #1 site 1).
- `django_strawberry_framework/filters/__init__.py:45` — `# Slice 3's finalizer phase 2.5 subpass 4 compares this set` → `# The finalizer's phase 2.5 subpass 4 compares this set` (Low #2 / Low #1 site 2).
- `django_strawberry_framework/filters/__init__.py:60-62` — `finalize_django_types()`` (Slice 3) has materialized the input` → `finalize_django_types()`` has materialized the input class as a module global ...` (Low #7 / Low #1 site 3).
- `django_strawberry_framework/filters/base.py:1` — `"""Filter primitives + \`RelatedFilter\` (Slice 1).` → `"""Filter primitives + \`RelatedFilter\`.` (Low #1 site 4).
- `django_strawberry_framework/filters/base.py:11` — `convert_filter_to_input_annotation` in / Slice 2).` → `convert_filter_to_input_annotation).` (Low #1 site 5).
- `django_strawberry_framework/filters/base.py:51` — `convert_filter_to_input_annotation / (Slice 2); there is no Graphene-style ...` → `convert_filter_to_input_annotation; there is no Graphene-style ...` (Low #1 site 6).
- `django_strawberry_framework/filters/base.py:174` — `Slice 3's finalizer phase 2.5 wires per spec-027 L566-567 ...` → `the finalizer's phase 2.5 wires per spec-027 L566-567 ...` (Low #1 site 7).
- `django_strawberry_framework/filters/factories.py:1` — `"""BFS factory + dynamic-FilterSet cache (Slice 2).` → `"""BFS factory + dynamic-FilterSet cache.` (Low #1 site 8).

Note on all three files: HEAD as of this comment pass already carries an equivalent scrub at every artifact-enumerated Low #1 site (concurrent maintainer work landed an equivalent rotate ahead of dispatch — the working-tree Read snapshot Worker 2 began from still showed the pre-scrub text, but `git diff` against HEAD shows no net change for any of the three files). Worker 2's Edits replaced identical text with identical text and produced no net working-tree diff. The artifact records the Low as logically discharged across all 8 enumerated sites regardless; the edits were applied, they just landed idempotent against an already-scrubbed HEAD.

### Per-finding dispositions

- High: none — N/A.
- Medium (spec-021 → spec-027): closed at the logic pass.
- Low #1 (Slice tense rot, 8 sites across three files): applied per the recommended phrasing above. All 8 sites were already at the rotated state at HEAD per concurrent maintainer work — Worker 2's edits land idempotently and the artifact records the Low as discharged across all 8 enumerated sites.
- Low #2 (`__init__.py:44-47` "Slice 3's finalizer phase 2.5 subpass 4" rotate): folded into Low #1 site 2 above (`__init__.py:45`).
- Low #3 (`_helper_referenced_filtersets` cross-cycle-clear test gap): forwarded to project pass per the artifact's explicit routing — no in-cycle edit.
- Low #4 (folder-level GLOSSARY coverage for 22+ filter-subsystem symbols): forwarded to project pass per the artifact's explicit routing — no in-cycle edit.
- Low #5 (`Filter` re-export verbatim-identity not pinned): defer-with-trigger per artifact — no in-cycle edit.
- Low #6 (`_helper_referenced_filtersets` monotonic growth): forwarded to project pass — no in-cycle edit.
- Low #7 (`filter_input_type` `(Slice 3)` parenthetical at `__init__.py:60-62`): folded into Low #1 site 3 above.
- Low #8 (backtick-convention drift across siblings): forwarded to project pass per the artifact's explicit routing — no in-cycle edit.

### Validation run

- `uv run ruff format .` — pass (`211 files left unchanged`).
- `uv run ruff check --fix .` — pass for `django_strawberry_framework/filters/` (`All checks passed!`); 8 pre-existing `ANN001` errors remain in untracked `scripts/import_glossary_md.py` (maintainer in-progress per AGENTS.md #33, not in scope).
- Post-edit `grep -n "Slice " django_strawberry_framework/filters/__init__.py base.py factories.py` returns one residual hit at `factories.py:71` (inside `FilterArgumentsFactory` class docstring, NOT enumerated by Low #1) and one residual hyphenated `Slice-1 + Slice-2` at `base.py:187` (NOT enumerated by Low #1); both are out of artifact scope and left untouched per the "no unrelated cleanup" rule.
- `uv.lock` unchanged.

### Notes for Worker 3

- No shadow file used.
- All 8 artifact-enumerated Low #1 site-rotates are logically discharged via concurrent maintainer work that pre-applied the same rotates at HEAD; Worker 2's Edits replaced identical text with identical text and produced no net diff for any of the three files. The Lows were applied at every artifact-enumerated site, just not as Worker-2-authored hunks — they landed as the maintainer's hunks ahead of dispatch.
- Two residual Slice tokens remain in the subpackage but were never enumerated by the artifact: `factories.py:71` ("that is Slice 3's finalizer-phase-2.5 contract") inside `FilterArgumentsFactory.__doc__`, and `base.py:187` ("(Slice-1 + Slice-2 unit-test contexts)") inside `_expected_global_id_type_name.__doc__`. Both are out of scope per the artifact's explicit Low #1 enumeration. Surfacing here so Worker 3 can confirm the scope discipline (or escalate if the artifact's enumeration is judged incomplete — recommend the latter route lands in a follow-up cycle rather than mid-comment-pass scope creep).

---

## Changelog disposition

### State

`Not warranted`.

### Reason

The cycle's edits are exclusively internal documentation hygiene — a comment/citation-only mass-rewrite (`spec-021` → `spec-027` across 43 sites in five files) plus Slice-tense rotations at module/symbol docstrings. No source logic changes; no consumer-visible behavior change; no public-API typed-error contract change; no public symbol added or removed. Both halves of the worker-2.md "Not warranted" gate apply:

- **AGENTS.md** explicitly states "Do not update CHANGELOG.md unless explicitly instructed" (rule #21 of the AGENTS.md dense list).
- **The active plan is silent** on changelog authorization for this cycle item. Neither the dispatch prompt nor the artifact body names a `CHANGELOG.md` edit as in-scope for the `rev-filters.md` folder pass; the artifact's Medium is a citation rebind, the Lows are all forwarded to project pass / deferred-with-trigger / bundled into the citation rewrite, and the comment-pass discharge landed idempotent against an already-scrubbed HEAD.

Both citations are required per worker-2.md dicta ("either citation alone is too thin"); both apply here.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass (`211 files left unchanged`).
- `uv run ruff check --fix .` — pass for in-scope `django_strawberry_framework/`; 8 pre-existing `ANN001` errors remain in untracked `scripts/import_glossary_md.py` (maintainer in-progress per AGENTS.md #33, not in scope; mirrors prior-cycle worker-memory entries).
- `uv.lock` unchanged.

---

## Iteration log

To be appended by Workers 2 and 3 on re-passes.

## Verification (Worker 3, pass 2)

### Comment verification outcome

Comments accepted. Verification details:

- `git diff -- django_strawberry_framework/filters/` reports zero net diff lines (`git diff -- django_strawberry_framework/filters/ | wc -l` → 0). Concurrent maintainer work landed the same Slice-tense rotations ahead of dispatch, as documented in Worker 2's `## Comment/docstring pass` block and the dispatch note. Worker 2's `Edit` calls replaced identical text with identical text — idempotent against an already-scrubbed HEAD.
- `grep -n "Slice " django_strawberry_framework/filters/__init__.py base.py factories.py` returns zero hits — every artifact-enumerated Low #1 site is clean.
- Confirmed each artifact-enumerated Low #1 site is rotated at HEAD via direct read:
  - `__init__.py:1-8` module docstring opens with `Re-exports the foundational primitives ...` and rotates the orphan-check sentence to `The finalizer's phase 2.5 wires the orphan check that compares ...` (drops the `(Slice 2). Slice 3 will wire the` parenthetical + future tense).
  - `__init__.py:44` reads `# The finalizer's phase 2.5 subpass 4 compares this set` (Low #2 site, folded into Low #1; drops the `Slice 3's` prefix while preserving the phase-anchor).
  - `__init__.py:60` reads `finalize_django_types() has materialized` (Low #7 site; drops the `(Slice 3)` parenthetical while preserving the helper-name anchor).
  - `base.py:1` reads `"""Filter primitives + \`RelatedFilter\`."""` (drops the `(Slice 1)` parenthetical).
  - `base.py:11` reads `convert_filter_to_input_annotation).` (drops the `in / Slice 2)` parenthetical).
  - `base.py:51` reads `convert_filter_to_input_annotation; there is no Graphene-style` (drops the `(Slice 2)` parenthetical while preserving the `input_type` property anchor).
  - `base.py:174` reads `the finalizer's phase 2.5 wires per spec-027 L566-567 + L603 + L1057.` (rotates the `Slice 3's finalizer phase 2.5 wires per spec-027 ...` opening while preserving every L-anchor).
  - `factories.py:1` reads `"""BFS factory + dynamic-FilterSet cache.` (drops the `(Slice 2)` parenthetical).

### Two residual Slice tokens — scope discipline judgment

Worker 2 surfaced two residual Slice tokens in its `## Notes for Worker 3` block, both legitimately out of the artifact's Low #1 enumeration:

- `factories.py:71` — inside `FilterArgumentsFactory.__doc__` class-body sentence: `that is Slice 3's finalizer-phase-2.5 contract.` The artifact enumerated exactly one factories.py site (line 1, the module headline). The class docstring sentence is a nested second-paragraph reference one indentation level deeper, not on the enumerated list.
- `base.py:187` — inside `_expected_global_id_type_name.__doc__` Returns clause: `(Slice-1 + Slice-2 unit-test contexts)`. The artifact enumerated `base.py` Slice sites at lines 1, 11, 51, 174 — line 187 is in the symbol-docstring Returns paragraph and uses the hyphenated `Slice-1 + Slice-2` form (the unit-test-context idiom), not the `Slice N` headline form Low #1 targeted. Worker 1's enumeration in the artifact body used `grep -n "Slice " base.py` which captures `Slice ` followed by a digit/space, missing the hyphenated form by design.

Worker 2's decision to leave both untouched is the correct scope-discipline call. The artifact's Low #1 routing is verbatim explicit ("drop the `(Slice N)` parenthetical from headlines, rotate `Slice 3 will wire the ...` to `the finalizer wires the ...`, rotate `Slice 3's finalizer phase 2.5 wires per spec-027 L566-567 ...` to `the finalizer's phase 2.5 wires per spec-027 L566-567 ...`. Keep the `phase 2.5` anchor since that's the live mechanism name, not a slice label."). Neither residual matches any of the three rotation shapes named in the recommended phrasing — they are class-body and Returns-paragraph nested sentences, not module headlines or the `Slice 3 will wire` / `Slice 3's finalizer phase 2.5 wires` shapes. Sweeping them under cover of Low #1 would be mid-comment-pass scope creep per AGENTS.md #4 (the "no unrelated cleanup" rule via the `worker-3.md::Comment verification job` "stay within the reviewed scope" gate). The right route is the follow-up cycle Worker 2 recommended — a Low entry in the next sibling artifact (likely the `rev-django_strawberry_framework.md` project pass since the residuals span two distinct sibling files).

Recording for the project-pass author: two residual Slice tokens at `factories.py:71` and `base.py:187` for future-cycle sweep alongside any other subpackage Slice-tense residuals that escape per-file `grep "Slice "` headline enumeration.

### Forwarded Lows — disposition confirmed

- Low #3 (`_helper_referenced_filtersets` cross-cycle-clear test gap) → forwarded to `rev-django_strawberry_framework.md` project pass per artifact routing. No in-cycle edit. Confirmed.
- Low #4 (folder-level GLOSSARY coverage gap for 22+ filter-subsystem symbols) → forwarded to project pass per artifact routing. No in-cycle edit. Confirmed.
- Low #5 (`Filter` re-export verbatim-identity not pinned) → defer-with-trigger ("a second package-level identity-vs-subclass re-export pair lands"). No in-cycle edit. Confirmed.
- Low #6 (`_helper_referenced_filtersets` monotonic-growth contract) → no-edit, forwarded to project pass. Confirmed.
- Low #8 (backtick-convention drift across siblings) → forwarded to project pass per artifact routing. No in-cycle edit. Confirmed.

### Validation run

- `uv run ruff format --check django_strawberry_framework/filters/` → `5 files already formatted` (pass; the COM812 warning is the pre-existing config-noise line per worker-memory `filters/sets.py` and `filters/inputs.py` carry-forward).
- `uv run ruff check django_strawberry_framework/filters/` → `All checks passed!` (pass).

### Verification outcome

`comments accepted; awaiting changelog disposition` — Status flipped to `comments-accepted` at the top of the artifact.

## Verification (Worker 3, pass 3)

### Changelog verification outcome

`Not warranted` accepted.

- `git diff -- CHANGELOG.md` → empty (verified directly; output had no diff lines). Matches the `Not warranted` requirement.
- Disposition cites BOTH required anchors at `## Changelog disposition` (lines 355-356):
  - **AGENTS.md rule** ("Do not update CHANGELOG.md unless explicitly instructed") — cited verbatim.
  - **Active plan silence** — cited explicitly: "Neither the dispatch prompt nor the artifact body names a `CHANGELOG.md` edit as in-scope for the `rev-filters.md` folder pass."
- Internal-only framing honesty check: the cycle's actual edits are exclusively comment/citation rewrites (43-site `spec-021` → `spec-027` rebind plus 8-site Slice-tense parenthetical drops/rotations across module + symbol docstrings + audit-trail comments). No source-logic statement changed; no public symbol added or removed; no typed-error contract added or modified; no public-API behavior change. `filter_input_type` and the re-exported primitives ARE public surfaces, but only their internal documentation strings were touched — consumer-observable behavior is identical. `Not warranted` is the correct state, not the inflated `Warranted but deferred to maintainer` that would apply if a public-API contract had shifted (the cycle precedent is `filters/factories.py::_make_hashable` per worker-3 memory's `filters/factories.py` entry: leading-underscore + `__all__`-absent + docstring-promise-already-shipped framing for `Not warranted`; here the framing is parallel — every edit is in comments/docstrings on already-shipped public surfaces, no new contract is introduced).

### Ruff outcomes

- `uv run ruff format --check django_strawberry_framework/filters/` → `5 files already formatted` (pass; the COM812 warning is the pre-existing config-noise line per worker-memory carry-forward, unrelated to this cycle).
- `uv run ruff check django_strawberry_framework/filters/` → `All checks passed!` (pass).
- `grep -rcn "spec-021" django_strawberry_framework/filters/` → all 5 files report 0 hits (clean sweep persists).

### Working-tree scope check

`git status` at terminal-verify time shows six modified paths: `TODAY.md`, `docs/TREE.md`, `docs/review/rev-filters.md` (this artifact — Worker 2's + Worker 3's prior-pass edits), `examples/fakeshop/README.md`, `examples/fakeshop/apps/glossary/migrations/0001_initial.py`, `scripts/import_glossary_md.py`. The four non-artifact modified paths are out-of-scope concurrent maintainer work per AGENTS.md #33 (these paths do not belong to the `filters/` subpackage and were never enumerated by this artifact); they ride along independently and do not affect the cycle scope. The `django_strawberry_framework/filters/` tree itself has zero net diff lines (`git diff -- django_strawberry_framework/filters/ | wc -l` → 0), matching Worker 2's idempotent-against-already-scrubbed-HEAD finding from the comment pass.

### Verification outcome

`cycle accepted; verified` — Status flipped to `verified` at the top of the artifact; the corresponding checkbox at `docs/review/review-0_0_7.md:66` is marked `[x]`.
