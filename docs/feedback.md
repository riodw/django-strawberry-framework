# Pre-merge review — `build-021-filters-0_0_8` → `main`

Reviewed: 110 `.py` files (~16K insertions), HEAD + uncommitted working-tree edits to
`filters/inputs.py`, `filters/sets.py`, `types/converters.py`,
`examples/fakeshop/apps/kanban/models.py`, three `test_query/*.py`, and
`tests/filters/test_sets.py`.

The branch is large but well-staged. The filters subsystem is the headline change
(~3K lines) and is where the review effort concentrated. The framework-core diff
(types / optimizer / registry) is mostly disciplined refactor plus one significant
finalizer expansion. Example apps and tests are additive and contain one shipped
broken module plus a handful of test-hygiene issues.

There is **one confirmed BLOCKER** (B1) that should not merge as-is, and a small
number of HIGH-severity findings that are worth fixing or pinning with a
regression test before the merge.

---

## TL;DR — what to fix before merging

1. **B1** — Nested `and`/`or`/`not` branches drop `RelatedFilter` constraints
   silently. ([filters / sets.py:1213-1218](django_strawberry_framework/filters/sets.py))
2. **H-core-3** — `_bind_filterset_owner` doesn't reject a `Meta.filterset_class`
   whose `Meta.model` differs from the owner-type's model. First binding passes
   through; the failure surfaces at query time, far from the cause.
   ([types/finalizer.py:270-358](django_strawberry_framework/types/finalizer.py))
3. **H-examples** — `examples/fakeshop/apps/products/aggregates.py` imports
   symbols the framework doesn't export (`RelatedAggregate`, `aggregates.AdvancedAggregateSet`).
   Currently dead but shipped. Delete or comment-fence.
4. **H-scripts** — `scripts/check_trailing_commas.py:147` skips every construct
   whose closing bracket sits at column 0 (the common ruff-formatted shape).
   The collapse pass is a silent no-op on most real targets.
5. **H-filters-1** — `getattr(settings, "HIDE_FLAT_FILTERS", False)` only catches
   `AttributeError`; the project's `Settings.__getattr__` raises
   `ConfigurationError` for malformed config, leaking it from finalize.
   ([filters/inputs.py:667](django_strawberry_framework/filters/inputs.py))

Everything else is HIGH-suspicion / MEDIUM / LOW and can land with a follow-up.

---

## BLOCKER

### B1 — Nested logic branches silently widen on `RelatedFilter` children

[`django_strawberry_framework/filters/sets.py:1213-1218`](django_strawberry_framework/filters/sets.py)

`_q_for_branch` normalizes `child_input` via `_normalize_input`, which strips
related-branch keys (sets.py:573-574, 589-592), then instantiates a sibling
`cls(data=child_data, queryset=queryset, ...)` and reads `.qs`. It never calls
`_apply_related_constraints` for the child branch. Practical effect: a query
shaped like

```graphql
filters: { or: [{ shelves: { code: { iContains: "A" } } }] }
```

produces a `child_data` dict with the `shelves` key removed, so the resulting
`pk__in=child_qs.values("pk")` is the un-constrained parent queryset — every
row passes. Any nested logical clause that references a related branch is
silently widened.

**Confirmed** via tracing `_normalize_input`'s strip path against
`_q_for_branch`'s reconstruction.

**Fix direction**: thread the original (un-normalized) `child_input` through
`_q_for_branch`, recompute `child_qs_by_branch =
cls._derive_related_visibility_querysets_*(child_input, info)` for the branch,
and call `_apply_related_constraints(child_input, queryset, child_qs_by_branch)`
before instantiation. This requires threading `info` (not just `request`)
through `_q_for_branch` — see M-filters-1.

**Regression test to add**: pin `or: [{shelves: {code: {iContains: "X"}}}]`
against a fixture that has shelves with non-matching codes; assert only matching
rows are returned, not the full set.

---

## HIGH

### H-filters-1 — `HIDE_FLAT_FILTERS` read can surface `ConfigurationError`

[`django_strawberry_framework/filters/inputs.py:667`](django_strawberry_framework/filters/inputs.py)

```python
hide_flat_filters = bool(getattr(settings, "HIDE_FLAT_FILTERS", False))
```

The 3-arg `getattr` only catches `AttributeError`. The project's
`Settings.__getattr__` raises `ConfigurationError` when
`DJANGO_STRAWBERRY_FRAMEWORK` is a malformed shape, so this access at finalize
time will propagate from a setting unrelated to filters.

**Fix**: either catch `ConfigurationError` explicitly or document that
`HIDE_FLAT_FILTERS` requires a valid (or absent) settings mapping.

### H-filters-2 — `apply_async` does not wrap user hooks in `sync_to_async`

[`django_strawberry_framework/filters/sets.py:1324-1332`](django_strawberry_framework/filters/sets.py)

`apply_async` constructs the filterset and reads `.qs` directly. Today this
is safe — chained `.filter()` calls and `.values("pk")` subqueries do no I/O.
But: nothing prevents a consumer-supplied `check_*_permission` or a custom
`method=` filter from doing a synchronous ORM hit, which would block the
event loop without raising.

**Fix**: at minimum, docstring note that `apply_async` does not wrap user
hooks; ideally `sync_to_async` the `.qs` read or document the contract loudly.

### H-filters-3 — `FilterArgumentsFactory` mutable class-attribute caches shared by subclasses

[`django_strawberry_framework/filters/factories.py:75-80`](django_strawberry_framework/filters/factories.py)

`input_object_types` and `_type_filterset_registry` are class-level dicts.
The docstring says don't subclass, but the class is public and Python won't
stop a consumer. State will leak silently across subclasses.

**Fix**: move both to `__init_subclass__` or detect subclassing and raise.

### H-filters-4 — `filter_for_lookup` Relay-PK guard only fires post-finalize

[`django_strawberry_framework/filters/sets.py:438-443`](django_strawberry_framework/filters/sets.py)

`_is_own_pk_under_relay_owner` requires `cls._owner_definition` to be bound,
which doesn't happen until phase-2.5. The docstring at line 432 calls it
"authoritative" but during class creation `_owner_definition` is `None`, the
check returns `False`, and the error never fires. Only during finalize's
`get_filters()` call does the error materialize.

**Fix**: update the docstring (it's authoritative post-finalize) or move the
Relay-aware check earlier in the metaclass pipeline.

### H-filters-5 — `BaseCSVFilter` element type uses `str` for custom-method CSV filters with int columns

[`django_strawberry_framework/filters/inputs.py:359`](django_strawberry_framework/filters/inputs.py)

The new `_element_annotation` helper handles model-field-driven scalar
inference correctly when `model_field` is supplied. Custom-method CSV filters
(`method=` shape) have `model_field=None`, fall through to
`_scalar_from_form_field`, and pick up `forms.CharField` from the CSV widget
wrapper — yielding `list[str]` even when the underlying column is `int`.

**Confirmed** but rare. Suggest documenting the contract or auto-inferring
from the resolver-method name when possible.

### H-filters-6 — `_field_specs` can carry stale entries across registry rebuilds (test-isolation risk)

[`django_strawberry_framework/filters/inputs.py:139, 878`](django_strawberry_framework/filters/inputs.py)

`clear_filter_input_namespace` is called via `registry.clear()`. Test suites
that reload model modules without going through `registry.clear()` will retain
stale `_field_specs` entries from the prior build. The
`_isolate_registry` autouse fixture in the filter test files compensates by
clearing several global ledgers explicitly — but consumer test suites won't.

**Fix**: either document the cleanup contract or hook the model-module reload
path.

### H-filters-7 — `_q_for_branch` does not invoke `_run_permission_checks` for child input

[`django_strawberry_framework/filters/sets.py:1213-1218`](django_strawberry_framework/filters/sets.py)

Today this is safe because `apply_sync` / `apply_async` walk the original
input through `_run_permission_checks` upfront (sets.py:966-994), which
recurses into nested branches. If a future caller bypasses `apply_*` and
reaches `filter_queryset` directly, permissions won't fire for nested
branches.

**Fix**: add a regression test pinning that `apply_*` is the only legal entry
point for permission-aware filtering, OR move the check into `_q_for_branch`.

### H-core-1 — Finalize-time exception rewrap loses original error class

[`django_strawberry_framework/types/finalizer.py:516`](django_strawberry_framework/types/finalizer.py)

```python
except Exception as exc:
    ...
    raise ConfigurationError("...expansion failed...")
```

`ConfigurationError` is re-raised cleanly (two lines above), but every other
exception type — `AttributeError` from a typo in a `RelatedFilter` field
name, `ImportError` from a bad module path — is rewrapped into a generic
"raised during expansion" message. The `__cause__` chain preserves the
detail; the top-of-screen consumer-visible message does not.

**Fix**: narrow the rewrap to a documented allowlist (`ImportError`,
`AttributeError`, `TypeError`), include `repr(exc)` in the message, and rely
on the existing `__cause__` chain.

### H-core-2 — `_resolve_field_map` dual-contract (FieldMeta vs raw Django field)

[`django_strawberry_framework/optimizer/walker.py:107-114`](django_strawberry_framework/optimizer/walker.py)

When a relation target has no registered DjangoType, the walker falls back to
raw Django field objects. `getattr`-everywhere makes this work in practice,
but the dual contract is undocumented in the walker module. The same
divergence already exists in `_field_meta_for_resolver`
([resolvers.py:182-212](django_strawberry_framework/optimizer/resolvers.py))
where it picked up a defensive fallback.

**Fix**: either build a `FieldMeta`-shaped map in the fallback branch (one
extra build per request for unregistered models, unified contract), or
document the dual contract loudly at the function returning the map.

### H-core-3 — `_bind_filterset_owner` doesn't reject obviously-wrong owners on first bind

[`django_strawberry_framework/types/finalizer.py:270-358`](django_strawberry_framework/types/finalizer.py)

The mismatch validation only triggers on a *second* owner binding. A consumer
who wires `Meta.filterset_class = ItemFilterSet` on a `CategoryType` (entirely
different model) gets through `types/base.py` validation (only checks
`issubclass(filterset_class, FilterSet)`) and through subpass 1 unimpeded.
The first symptom is at query time — wrong model, opaque traceback.

**Fix**: in `_bind_filterset_owner`, when `previous is None`, also assert
`definition.model is filterset_cls._meta.model` (or a subclass relationship)
and raise `ConfigurationError` with both model names. This is the single most
common Phase-2.5 user-error and would surface it loudly at finalize.

### H-examples — `apps/products/aggregates.py` is broken-on-import dead code

[`examples/fakeshop/apps/products/aggregates.py`](examples/fakeshop/apps/products/aggregates.py)

`from django_strawberry_framework import RelatedAggregate` raises `ImportError`;
the symbol does not exist. Also references `aggregates.AdvancedAggregateSet`
which is not defined anywhere. The file is currently unreferenced, but
`apps/products/schema.py:58` contains a commented hint to enable it — a user
following the hint hits an import error before reaching any feature-not-ready
signal. Additionally, line 18 uses `super(type(self), self)` (the classic
infinite-recursion-under-subclassing anti-pattern), so even if the imports
landed, the class would be misleading reference material.

**Fix**: delete the file or wrap its body in `if TYPE_CHECKING:` with a
TODO-BETA-040 comment.

### H-scripts — `check_trailing_commas.py` skips column-0 closers

[`scripts/check_trailing_commas.py:147`](scripts/check_trailing_commas.py)

The self-verify guard reads `not (0 < close_byte <= len(close_bytes))`. For
a top-level multi-line literal whose `]` lands at column 0 (the standard
ruff-formatted shape), `close_byte == 0`, the strict `0 <` rejects it, and
the construct is silently dropped. The collapse direction is a no-op on the
majority of real targets.

**Fix**: change to `0 <= close_byte < len(close_bytes)` (two-character fix).

---

## MEDIUM

### filters subsystem

- **M-filters-1** [`sets.py:1189-1218`](django_strawberry_framework/filters/sets.py) — `_q_for_branch` accepts `request` but not `info`. Signature mismatch with `apply_sync` is a latent footgun if `check_*_permission` or related-target hooks start consulting `info`.
- **M-filters-2** [`sets.py:395-408`](django_strawberry_framework/filters/sets.py) — `filter_for_field` passes `**default.extra` blindly to `own_pk_filter_class`. `GlobalIDMultipleChoiceFilter` extends `MultipleChoiceFilter` which requires `queryset` or `choices`. SUSPICION; depends on how `default.extra` is populated.
- **M-filters-3** [`sets.py:593`](django_strawberry_framework/filters/sets.py) — `_normalize_input` keys `_field_specs` on `(cls, python_attr)`. A FilterSet subclass that inherits without rebuilding misses the related-branch source paths. SUSPICION — depends on whether subclassing is supported per design.
- **M-filters-4** [`factories.py:39`](django_strawberry_framework/filters/factories.py) — `_dynamic_filterset_cache` has no clear hook. After `registry.clear()`, dynamic FilterSets built against reloaded model classes leak.
- **M-filters-5** [`base.py:335-354`](django_strawberry_framework/filters/base.py) — `RelatedFilter.bind_filterset` silently no-ops on re-bind. If a single `RelatedFilter` instance is shared between subclasses through inheritance, the first owner sticks and subclasses get the wrong `bound_class.__module__` for unqualified string targets. SUSPICION.
- **M-filters-6** [`sets.py:1215`](django_strawberry_framework/filters/sets.py) — `_q_for_branch` deep-copies `base_filters` per branch (upstream `BaseFilterSet.__init__`). Perf scales with branches × filters. Performance suspicion, not correctness.

### framework core

- **M-core-1** [`base.py:598`](django_strawberry_framework/types/base.py) — Typo-guard `declared = {k for k in meta.__dict__ ...}` correctly uses `meta.__dict__`, but mutual-exclusion uses `getattr` which walks MRO. Asymmetry is intentional per the comment; document for posterity so future validators don't silently treat inherited keys as declared.
- **M-core-2** [`finalizer.py:367-368`](django_strawberry_framework/types/finalizer.py) — `_format_owner_mismatch_error` type-hints `prev_target` as `object`; should be `models.Field`. Type-hint-only, harmless at runtime.
- **M-core-3** [`finalizer.py:531-537`](django_strawberry_framework/types/finalizer.py) — `_helper_referenced_filtersets` may carry stale entries from pre-reload module classes, producing spurious orphan errors. Document the test-isolation dependency or hook the reload path.
- **M-core-4** [`filters/inputs.py:897-909`](django_strawberry_framework/filters/inputs.py) — `clear_filter_input_namespace` early-returns on `ImportError` from `filters.sets`, skipping the FilterSet-subclass attribute wipe. Defense-in-depth that may never fire in practice; split the two cleanup phases so neither blocks the other.

### example apps

- **M-examples-1** [`config/settings.py`](examples/fakeshop/config/settings.py) — No `DJANGO_STRAWBERRY_FRAMEWORK = {"HIDE_FLAT_FILTERS": True}` set. With per-field `"__all__"` everywhere and ~10 `RelatedFilter` declarations on `CardFilter` alone, the GraphiQL introspection surface shows the doubled-up flat-traversal form. The framework tests cover both toggle positions; the dogfooding schema does not demonstrate the cleaner shape.

### tests

- **M-tests-1** [`tests/filters/test_base.py:210-227`](tests/filters/test_base.py) — Monkey-patches `GlobalIDMultipleChoiceFilter.__mro__[1].filter` directly, writing through to the upstream `django_filters.MultipleChoiceFilter`. Try/finally restores, but: (a) race-prone under `pytest-xdist --dist loadscope`, (b) silently restores onto a different class if MRO changes. Switch to `monkeypatch.setattr(GlobalIDMultipleChoiceFilter.__mro__[1], "filter", spy)`.

### scripts

- **M-scripts-1** [`check_trailing_commas.py:_tokenize_info`](scripts/check_trailing_commas.py) — Counts positional-only `/` and keyword-only `*` markers as parameters. `def m(self, /)` reports 2 params; under the `models.py` threshold of 2, the fixer explodes a 1-arg method to `def m(self, /,):`. Syntactically legal, semantically wrong. Skip depth-1 tokens whose string is `/` or `*` (where `*` is not followed by an identifier).
- **M-scripts-2** [`check_trailing_commas.py:288`](scripts/check_trailing_commas.py) — Nested-trailing-comma guard regex `,\s*[)\]}]` can false-positive on single-line string literals containing those byte sequences. Rare; degraded behavior, not correctness.
- **M-scripts-3** [`check_trailing_commas.py:_run_ruff_format`](scripts/check_trailing_commas.py) — `subprocess.run(..., check=False)` swallows non-zero ruff exit. Surface the exit code on stderr.

---

## LOW / NIT (representative; full list in source review)

- `filters/__init__.py` re-exports `django_filters.Filter` under the package namespace. Shadow with a thin subclass or document.
- `filters/inputs.py:75-102` `LOOKUP_NAME_MAP` reverse walk in `_form_key_for_python_attr` is O(n) per call. Build the reverse map once at module scope.
- `filters/sets.py:205` class-level `_logic_depth: int = 0` annotation-with-default — drop the `= 0` for a pure annotation or document intent.
- `finalizer.py:546` bare expression statement `factory.arguments` for side effects. `_ = factory.arguments` reads cleaner.
- `finalizer.py:414` single-orphan format uses `cls.__name__`; multi-orphan uses `cls.__module__.{cls.__qualname__}`. Match formats.
- `test_finalizer.py:680` subprocess test uses `sys.path.insert(0, 'examples/fakeshop')` — relative path assumes pytest cwd. Use `__file__`-derived absolute path.
- `test_sets.py:1419-1438` direct attribute assignment (`BookFilter._owner_definition = object()`) breaks silently if those attrs become descriptors.
- `examples/fakeshop/db.sqlite3` is committed and grows 5x to 1.6MB. Seed on demand rather than tracking.
- `examples/fakeshop/test_query/test_products_api.py:102,114,134` interpolates Faker `category.name` raw into a GraphQL string. `json.dumps` would harden.
- `scripts/build_kanban_dashboard.py:387` raises `KeyError` for malformed GraphQL responses lacking both `errors` and `data`. One-line `.get` guard for legibility.
- `scripts/build_kanban_dashboard.py:362-367` mutates `sys.path` / `os.environ` and never undoes them. Fine for a top-level script; document if it ever becomes importable.

---

## Strengths

### filters subsystem
- Pipeline ordering in `apply_sync`/`apply_async` (visibility → constraints → permission → form validate → qs) is correct and commented; ordering rationale preserved.
- `_element_annotation` is a clean factor-out of three previously-divergent scalar/choice-enum branches.
- Dual `_is_own_pk_under_relay_owner` guard in both `get_fields` and `filter_for_lookup` mirrors spec-021 H1's intent.
- `_make_cache_key` / `_make_hashable` carefully handle dict-as-unordered vs list-as-ordered semantics with explicit fallback notes.
- GlobalID validation through `_expected_global_id_type_name` + `_decode_and_validate_global_id` surfaces type-name mismatches at filter time with the offending element index.
- Recursion-depth guard exposed as `ClassVar` so consumers can override without monkey-patching.
- `clear_filter_input_namespace` is thoughtful about what it does NOT do; the rationale for leaving module-globals parked is documented.

### framework core
- Failure-atomic Phase 1 in `finalizer.py` — unresolved-target audit completes before any class mutation, so retries don't leak partially-finalized state.
- Per-instance `_related_target_cache` keys cacheability on `registry.is_finalized()` — avoids locking in transient `None` lookups.
- `SyncMisuseError` multiply-inherits `ConfigurationError` + `RuntimeError` so both `except` paths work.
- `scalar_for_field` extraction cleanly de-duplicates the MRO walk between full DjangoType conversion and the filter-input converter.
- Plan-cache origin-keying carry-through (walker → extension → cache key) keeps the spec-014 regression closed.

### example apps
- Kanban app exercises filter paths nothing else in the example tree reaches: self-referential M2M (`dependencies`), through-model (`ParityClaim`), reverse-FK (`outgoing_references`), and a deliberately-non-Relay sibling type (`CardItemType`). Strong dogfooding.
- UUIDModel one-hot DB constraint + the three accept-one/reject-zero/reject-multi tests are a useful teaching pattern.
- Working-tree regression tests in three `test_query/*_api.py` files lock real coercion bugs found on this branch (isNull-on-Relay-PK, enum-in-list, BigInt-in-list).

### tests
- `tests/filters/test_sets.py` (74 tests, 1796 lines) covers the whole apply pipeline including a spy-`__init__` test pinning constrained-queryset ordering without depending on internal state.
- `tests/filters/test_finalizer.py` covers all four phase-2.5 subpasses including a subprocess test for the cycle-safe `registry.clear()` contract.
- `tests/filters/test_inputs.py:74` pins LOOKUP_NAME_MAP verbatim — defends against accidental camelCase drift.

### scripts
- All `subprocess.run` calls are list-form (no shell-injection vectors).
- `check_trailing_commas.py` re-parses every fixed file with `ast.parse` before writing.
- `check_trailing_commas.py` reads `line-length` from `pyproject.toml` — fixer can't drift from formatter target.
- `build_kanban_dashboard.py:396` escapes `</` → `<\/` in embedded JSON. XSS hygiene that's easy to forget.
- The diff helper / snapshot helper refactor eliminates ~100 lines of duplicated git/subprocess plumbing.

---

## Files reviewed

**Framework** — `django_strawberry_framework/filters/{__init__,base,factories,inputs,sets}.py`,
`django_strawberry_framework/sets_mixins.py`, `django_strawberry_framework/types/*.py`,
`django_strawberry_framework/optimizer/*.py`, `django_strawberry_framework/registry.py`,
`django_strawberry_framework/conf.py`, `django_strawberry_framework/__init__.py`,
`django_strawberry_framework/utils/relations.py`.

**Examples** — `examples/fakeshop/apps/{kanban,library,products,scalars}/**/*.py`,
`examples/fakeshop/config/{schema,settings}.py`, `examples/fakeshop/test_query/*.py`.

**Tests** — `tests/filters/*.py` (new), `tests/types/*.py`, `tests/optimizer/*.py`,
`tests/utils/*.py`, `tests/test_*.py`, `tests/base/*.py`.

**Scripts** — `scripts/*.py`, `line_count.py`.

---

## Recommendation

Hold the merge until B1 is fixed (with a regression test pinning the
nested-`or` + `RelatedFilter` shape). The four other HIGH items (H-core-3,
H-examples, H-scripts, H-filters-1) can either be fixed in the same prep
or land as immediate follow-ups; H-core-3 in particular is cheap and prevents
a category of opaque finalize-time bugs. Everything else can roll forward
through normal grooming.
