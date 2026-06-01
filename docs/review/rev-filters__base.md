# Review: `django_strawberry_framework/filters/base.py`

Status: verified

## DRY analysis

- **Collapse `ArrayFilter.method` setter + `ListFilter.method` setter via a shared `_typed_method_setter(filter_class, method_class)` helper.** `base.py:93-98` and `base.py:156-161` are token-identical except for the substituted `*FilterMethod` class:
  - both call `TypedFilter.method.fset(self, value)`
  - both guard `if value is not None`
  - both reassign `self.filter = <FooFilterMethod>(self)`
  The pair was correct as a verbatim two-site upstream port (graphene's `array_filter.py` + `list_filter.py`), but the two siblings now live in the same module, sit ~60 lines apart, and the call sites involved are the only two. **Defer until a third `TypedFilter` subclass adopts the same setter-swap pattern** (e.g. a future `RangeMethod` or any consumer-facing `TypedFilter` port that needs empty-list-as-value semantics); a shared helper at two sites would obscure the per-class wiring without saving meaningful code. Re-triage when a third site lands.
- **Collapse `ArrayFilterMethod.__call__` and `ListFilterMethod.__call__` via a single shared `EmptyListAwareFilterMethod` base.** `base.py:55-62` and `base.py:137-144` are byte-identical (same `if value is None: return qs; return self.method(qs, self.f.field_name, value)` body). The current factoring keeps the two names alive because the Graphene cookbook ships two separate classes that `isinstance()` checks elsewhere can discriminate; `filters/inputs.py:445-449` does `isinstance(filter_instance, (ListFilter, ArrayFilter))` but does NOT discriminate on the `*FilterMethod` type. **Defer until a fourth `FilterMethod` subclass lands or until `isinstance(method, ArrayFilterMethod)` becomes load-bearing somewhere outside `base.py`** — at two sites with a shared name-as-discriminator role, the duplication is intentional sibling design.
- **Hoist `_global_id_filter_with_owner`-style fake-owner harnesses from `tests/filters/test_base.py:462-497` into a shared `tests/filters/_fakes.py` helper.** The `_FakePk` / `_FakeMeta` / `_FakeModel` / `_FakeTargetDefinition` / `_FakeOwnerDefinition` / `_FakeParent` chain at `tests/filters/test_base.py:462-497` is a hand-rolled owner-definition mock that future filter tests (e.g. `tests/filters/test_finalizer.py`, the planned `test_sets.py` GlobalID validation tests) will likely need too. **Defer until a second test module needs the fake-owner harness**; today the four owner-aware tests at `tests/filters/test_base.py:500-525` are the only consumers and a shared module would just split context.

## High:

None.

## Medium:

None.

## Low:

### `RelatedFilter.lookups` constructor kwarg is stored but never read

`base.py:323-333` accepts a `lookups: list[str] | None = None` kwarg and stores it as `self.lookups = lookups or []`, but nothing in the package ever reads `RelatedFilter.lookups` back:

```django_strawberry_framework/filters/base.py:323-333
    def __init__(
        self,
        filterset: str | type[BaseFilterSet],
        *args,
        lookups: list[str] | None = None,
        **kwargs,
    ) -> None:
        self._has_explicit_queryset = kwargs.get("queryset") is not None
        super().__init__(*args, **kwargs)
        self._filterset = filterset
        self.lookups = lookups or []
```

A `grep -rn "\.lookups" django_strawberry_framework/ examples/fakeshop/ tests/` confirms zero readers — the `.lookups` references in the codebase are either unrelated (`_prefetch_related_lookups` on QuerySets, `django.db.models.lookups` imports) or write-side at `base.py:333`. The upstream cookbook (`/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/filters.py:120-126`) stores the same kwarg under the same dead-state condition — the cookbook's `input_data_factories.py:110,142` `input_type.lookups` references are reads of a generated input type's `.lookups`, not the filter instance's. So this is a verbatim port of an upstream dead kwarg.

Spec-027 (the filter spec — see also forward below) does NOT name `lookups` as a `RelatedFilter` contract. The current shape silently accepts the kwarg without honoring or rejecting it, so a consumer passing `RelatedFilter(BookFilter, lookups=["exact", "in"])` gets no expansion AND no error. Two acceptable shapes:

1. **Drop the kwarg and the storage** — the cleaner fix; the cookbook artifact does not need to survive the port if nothing in the package consumes it. Test: add a regression `test_related_filter_rejects_lookups_kwarg` pinning the new shape if dropped.
2. **Wire `lookups` into the BFS factory's per-relation lookup expansion** — the upstream-faithful fix; the kwarg becomes a per-RelatedFilter override of the auto-derived lookup set. This is feature work, not citation hygiene, and probably belongs in a follow-on spec card.

Recommend (1) for 0.0.7 review — it's a citation-hygiene-class change, removes a misleading kwarg from the consumer surface, and the no-tests-need-touching outcome is the right loud-fail shape. If the maintainer wants to preserve the kwarg as a future hook, leave it but rename to `_lookups` (underscored) so callers can't pass it through the public constructor.

### `spec-021` source citations in this file actually point at `docs/SPECS/spec-027-filters-0_0_8.md`

`base.py` cites `spec-021` ten times (module docstring + every `_expected_global_id_type_name` / `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` / `RelatedFilter` docstring; lines 3-4, 22, 174, 185, 190, 217, 238, 244, 247, 269, 282, 309), but `docs/SPECS/spec-021-apps-0_0_7.md` is the **`apps.py` AppConfig** spec (514 lines, zero mentions of `RelatedFilter` or `lookups`). The actual filter spec is `docs/SPECS/spec-027-filters-0_0_8.md` (1290 lines, defines Decisions 2/3/4/9/11, has L566-567, L988, L1057, L602, L603, L605, etc.). The same sweeping mis-anchor appears across the entire `filters/` subpackage (`base.py`, `factories.py`, `__init__.py`, `inputs.py`, `sets.py` — 35+ hits per `grep -rn "spec-021" django_strawberry_framework/filters/`).

This is NOT a per-file `base.py` fix — sweeping `spec-021` → `spec-027` across one sibling without sweeping the other four would create internal inconsistency. **Forwarded to the folder pass `docs/review/rev-filters.md`** to mass-rewrite the whole filter subpackage in a single change. If the maintainer disagrees and the convention was "spec-021 is the working name for the filter design" rather than literal cross-file anchor, the right fix is to flip the file paths from `spec-021-apps-0_0_7.md` → `spec-027-filters-0_0_8.md` in the rename and update KANBAN; but the path on disk says spec-021 is the apps spec, and that decision was already shipped through `DONE-021-0.0.7`.

### `_GlobalIDMultipleChoiceField` docstring mixes `` `` and `"""` backtick conventions

`base.py:261-272` uses RST-style double-backticks (` ``MultipleChoiceField`` `) for inline-code spans whereas sibling docstrings in this file (e.g. `_expected_global_id_type_name` at `base.py:171-191`, `GlobalIDFilter` at `base.py:234-249`, `RelatedFilter` at `base.py:305-321`) use single-backticks (`` `MultipleChoiceField` ``). Other internal `base.py` docstrings (e.g. `TypedFilter`, `ArrayFilter`, `RangeFilter`, `ListFilter`) consistently use single-backticks. The `_decode_and_validate_global_id` docstring at `base.py:214-222` is also RST-style. This is purely a comment-pass consistency Low — pick one convention. Single-backtick matches the rest of the package; the RST convention is fine if applied package-wide but it isn't.

### `RelatedFilter.bind_filterset` "silent-no-op contract" docstring forwards to `_bind_filterset_owner` but the actual handler is `_bind_filtersets`'s subpass 1 + `_bind_filterset_owner`

`base.py:344-352` cites:

```django_strawberry_framework/filters/base.py:344-352
        Silent-no-op contract:
            A second call with a DIFFERENT ``filterset`` (the rare case
            of a module-level ``RelatedFilter`` instance shared across
            two ``FilterSet`` subclasses) is also silenced here. The
            strict cross-owner mismatch detection runs later at
            finalize time in
            ``types/finalizer.py::_bind_filterset_owner`` (H2-rev8
            check), so a real divergent-owner reuse still surfaces a
            ``ConfigurationError`` with both owners named — just not at
            class-creation time.
```

The cited `_bind_filterset_owner` does exist (`types/finalizer.py:271` per earlier grep), and the docstring is correct in pointing readers there. The only Low here is the implicit assumption that readers know `_bind_filterset_owner` is reached through the four-subpass `_bind_filtersets()` umbrella per `types/finalizer.py:483` — naming the umbrella would help a future reader trace the cascade. Suggested phrasing: `types/finalizer.py::_bind_filterset_owner (subpass 1 of finalizer phase 2.5's _bind_filtersets umbrella)`. Comment-pass territory; do not bump severity.

### GLOSSARY coverage gap for the five `base.py` shipped primitives is forwarded, not a local fix

The shipped public symbols `TypedFilter`, `ArrayFilter`, `ArrayFilterMethod`, `RangeFilter`, `RangeField`, `ListFilter`, `ListFilterMethod`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, and `LazyRelatedClassMixin` are exported through `django_strawberry_framework.filters` (`filters/__init__.py:91-107`) and live in `__all__`, yet `docs/GLOSSARY.md` has anchors only for `FilterSet`, `filter_input_type`, `Meta.filterset_class`, and `RelatedFilter` (and `RelatedFilter`'s entry at `docs/GLOSSARY.md:822-830` has `**Status:** shipped (0.0.8)` — see status forward below). The seven `TypedFilter`-family + GlobalID + mixin entries are absent. This pairs with the `sets_mixins.py` finding from the previous cycle (per `worker-memory/worker-1.md` "sets_mixins.py" carry-forward — all four `LazyRelatedClassMixin` / `ClassBasedTypeNameMixin` symbols also absent). **Forwarded to `rev-django_strawberry_framework.md`** because these are public-surface symbols whose first cohort of GLOSSARY coverage is best authored together with `FilterSet` / `Meta.filterset_class` reactivation; per worker-1.md the project pass owns this cross-file coverage call.

### `RelatedFilter` GLOSSARY entry says `shipped (0.0.8)` but lives in a `0.0.7` ship cohort

`docs/GLOSSARY.md:822-830` shows `## RelatedFilter` with `**Status:** shipped (0.0.8)`. The Worker 0 prompt says the cycle baseline is HEAD on a `0.0.7` release and `pyproject.toml` / `__init__.py` pin to `0.0.7` per `docs/review/review-0_0_7.md` line 4. But `RelatedFilter` itself is implemented at `base.py:304-401` and shipped through `filters/__init__.py`'s public surface today — the `shipped (0.0.8)` status is forward-dated, which matches `spec-027-filters-0_0_8.md`'s joint-cut deferral wording in spec-027 line 4 ("Slice 5 ... [docs/README.md ... version-bump promotion] deferred per Decision 10's joint-cut safe-default"). So the GLOSSARY label is consistent with the joint-cut deferral pattern, not a bug — RelatedFilter is shipped in source today AND will be labeled `(0.0.8)` whenever the version bump lands. **No edit needed**; flagged for visibility so a future reviewer doesn't mis-fix it. This is the same "joint-cut safe-default" the `sets_mixins.py` review carried forward; consistent treatment across siblings.

## What looks solid

### DRY recap

- **Existing patterns reused.** `RelatedFilter` defers all string/callable/class resolution to `LazyRelatedClassMixin.resolve_lazy_class` (`base.py:377-381`) — the canonical helper home in `sets_mixins.py` per the previous cycle. No duplication of the resolver logic here. `RelatedFilter` also delegates `bind_filterset`'s idempotency to a simple `hasattr` guard (`base.py:366-367`) rather than re-implementing the registry's snapshot-and-restore shape — load-bearing simplicity per `worker-memory/worker-1.md` carry-forward on registry.py ("intentionally divergent on primary handling"). The GlobalID decode flow is consolidated through `_decode_and_validate_global_id` (`base.py:208-230`) so both `GlobalIDFilter.filter` (`base.py:252-257`) and `GlobalIDMultipleChoiceFilter.filter` (`base.py:294-301`) share one decode/validate path; the per-element variant just adds the `index=` kwarg for spec-027 L605 error positioning.
- **New helpers considered.** Considered (a) extracting a shared `_typed_method_setter` for the `ArrayFilter.method` / `ListFilter.method` setters at `base.py:93-98` and `base.py:156-161` and (b) collapsing `ArrayFilterMethod.__call__` + `ListFilterMethod.__call__` into one base class. Both rejected for now — the two siblings are intentional verbatim ports of the corresponding graphene-django primitives and the names participate in downstream `isinstance` checks (`filters/inputs.py:445-449`). Both deferred with explicit triggers in `## DRY analysis` above. Also considered hoisting the test-side `_FakeOwnerDefinition` chain (`tests/filters/test_base.py:462-497`) into a shared fixtures module; rejected at one consumer per the same trigger discipline.
- **Duplication risk in the current file.** `ArrayFilter.method` setter and `ListFilter.method` setter are token-identical except for the `*FilterMethod` class substitution; `ArrayFilterMethod.__call__` and `ListFilterMethod.__call__` are byte-identical. Both are intentional sibling design — the two filter primitives carry independent `lookup_expr` semantics (`ArrayField` `__contains` / `__overlap` / `__contained_by` vs. `ListFilter` `__in`-family lookups), and the matching `*FilterMethod` discriminator names exist so `inputs.py` can `isinstance`-route per filter shape. Worker 2 should NOT collapse without the trigger conditions above firing.

### Other positives

- **Empty-list-as-value contract is documented load-bearing prose, not just code.** `ArrayFilter`'s docstring (`base.py:65-91`) explicitly enumerates the three `lookup_expr`-dependent semantics of `[]` (matches-all under `__contains`, matches-none under `__overlap`, matches-empty-only under `__contained_by`) and gives consumers a "want any-of" alternative — that's the right shape for a fragile contract that diverges from `FilterMethod`'s default `EMPTY_VALUES` short-circuit. `tests/filters/test_base.py:74-89` pins the lookup-expression-agnostic call shape (`{"tags__exact": []}`) so the empty-list-as-value contract is regression-pinned.
- **`_decode_and_validate_global_id` accepts both `str` and `relay.GlobalID` per spec-027 L602 (cited as L602 of "spec-021" — see Low #2 about the citation drift) and propagates the `index` kwarg only from `GlobalIDMultipleChoiceFilter.filter` so the error message names the rejected list element.** That's the spec-027 L605 contract honored verbatim; tests at `tests/filters/test_base.py:210-227` pin the per-element decode shape via `monkeypatch` on the parent class so the test does NOT mutate upstream state (xdist-safe).
- **`_expected_global_id_type_name` returns `None` for the Slice-1/2 unit-test path** (`base.py:194-195`) when `parent._owner_definition` is unbound, so the filter decodes the GlobalID without type-name validation — exactly the no-owner-context fallback per spec-027 L1057, and `tests/filters/test_base.py:500-504` pins this branch. The own-PK branch at `base.py:198-200` and the relation branch at `base.py:201-205` are pinned independently at `tests/filters/test_base.py:507-525`.
- **`RelatedFilter.bind_filterset` is idempotent via a single `hasattr` guard** (`base.py:366-367`) — the cookbook's two-class collapse (per `base.py:307-312` audit-trail docstring) is preserved as a single-class symbol per spec-027 Decision 2. The silent-no-op contract is explicit (`base.py:342-352`) AND defers the loud-fail to finalizer phase 2.5's `_bind_filterset_owner` so cross-owner reuse still surfaces a `ConfigurationError` at finalize — the right "fail loud at finalize, not at class-creation" pattern carried over from registry.py.
- **`RelatedFilter._has_explicit_queryset` ledger** (`base.py:330`) captures the explicit-vs-derived intent at construction time and reads through to the GLOSSARY's "filter-scope constraint, NOT a security boundary" contract at `docs/GLOSSARY.md:828` — the `get_queryset` override at `base.py:387-401` honors the explicit `queryset=` verbatim and only falls back to `target._meta.model._default_manager.all()` when no explicit queryset was supplied. Tests at `tests/filters/test_base.py:341-356` pin both branches.
- **`_GlobalIDMultipleChoiceField.valid_value` carries a precise audit-trail docstring** (`base.py:261-272`) explaining the empty-`choices` rejection problem upstream `MultipleChoiceField` has, and the `# noqa: ARG002 - signature fixed by Django` comment at `base.py:274` correctly hangs the noqa off the Django-API constraint.
- **`TYPE_CHECKING` import block at `base.py:39-41` carries `# pragma: no cover - type-checking-only import.`** — the same conditional-import + pragma shape used elsewhere in the package, correct per `AGENTS.md` "pragma no cover is only for branches genuinely unreachable under the test runner".

### Summary

`base.py` is a 401-line port of the upstream `graphene_django/filter/filters/*.py` primitives plus the `BaseRelatedFilter` + `RelatedFilter` collapse per spec-027 Decision 2. Every primitive carries a verbatim-port audit-trail docstring and the empty-list-as-value contract for `ArrayFilter` / `ListFilter` is documented load-bearing prose (not just code). The GlobalID decode/validate flow is consolidated through one helper (`_decode_and_validate_global_id`), the owner-aware type-name resolution (`_expected_global_id_type_name`) carries the spec-027 L1057 no-owner fallback, and `RelatedFilter` reuses `LazyRelatedClassMixin.resolve_lazy_class` for the string/callable/class resolution. Five Lows total: one logic-shape Low (`RelatedFilter.lookups` is dead state — verbatim upstream port artifact, recommend dropping it or underscoring), three citation/consistency Lows (the sweeping `spec-021` → `spec-027` anchor drift across the whole `filters/` subpackage is forwarded to the folder pass; backtick-convention drift in the GlobalID block; `_bind_filterset_owner` umbrella name), and one project-pass forward (GLOSSARY coverage for the seven `TypedFilter`-family + GlobalID + mixin symbols). No High / no behavior-changing Medium; the only logic-class Low is `RelatedFilter.lookups`, which is a small surface tightening, not a bug. Standard three-spawn cycle — the `lookups` Low needs a real edit AND tests; not a shape-#5 candidate.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/filters/base.py:323-332` — applied Low #1: dropped the `lookups: list[str] | None = None` kwarg from `RelatedFilter.__init__` and removed the `self.lookups = lookups or []` storage line. The constructor signature is now `(self, filterset, *args, **kwargs)`; the `_has_explicit_queryset` ledger and `super().__init__` call are preserved verbatim.

### Tests added or updated

- `tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg` — new regression pinning the kwarg removal: constructing `RelatedFilter("ShelfFilter", lookups=["exact", "in"])` raises `TypeError`. Placed in the RelatedFilter section immediately after `test_related_filter_explicit_queryset_ledger_defaults_false_when_absent` per `AGENTS.md` test-placement rules (package-level test, system under test is `django_strawberry_framework.filters.base.RelatedFilter`).

### Validation run

- `uv run ruff format .` — pass (183 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)
- pytest NOT run per Worker 2 hard rule; the regression-test assertion was confirmed by reading the new constructor signature (no `lookups` parameter; `**kwargs` is forwarded to `ModelChoiceFilter.__init__`, which raises `TypeError` for unknown kwargs).

### Notes for Worker 3

- **Grep evidence that `RelatedFilter.lookups` had zero readers.** Two-pass sweep over the entire package + example project + tests:
  - `grep -rn "\.lookups" django_strawberry_framework/ examples/ tests/` returned exactly one hit inside the package (`django_strawberry_framework/filters/base.py:333: self.lookups = lookups or []` — the WRITE that this change removes). All other `.lookups` hits are unrelated Django ORM imports (`django.db.models.lookups.Exact` in example-project migrations + one `apps/kanban/models.py` import).
  - `grep -rn "lookups=" django_strawberry_framework/ examples/ tests/` returned NO matches anywhere — no consumer (production, example, or test) ever passed the kwarg. So the regression test is the FIRST caller in repo history that exercises the removed kwarg path, and it does so to confirm it now raises.
- **Lows 2/3/4/5 deferred per dispatch prompt.** Low #2 (`spec-021` → `spec-027` drift) is forwarded to the folder pass `rev-filters.md` per the artifact itself; not touched here. Lows #3 + #4 are comment-pass items per the artifact's severity classification; will be addressed in the comment pass spawn after Worker 3 accepts this logic pass. Low #5 (GLOSSARY) is forwarded to the project pass per the artifact.
- **No shadow file consulted.** Edit was localized to the `__init__` body; no need to re-run `scripts/review_inspect.py`.
- **No `uv.lock` touch.** Confirmed via `git status` post-edit — `uv.lock` is not modified.
- **Pre-existing dirty paths left untouched** per AGENTS.md rule 33: `django_strawberry_framework/exceptions.py`, `list_field.py`, `scalars.py`, `sets_mixins.py`, and `docs/GLOSSARY.md` + `docs/feedback.md` + `docs/spec-028-orders-0_0_8.md` were already modified at task start (prior cycles' work) and were NOT touched by this pass.

---

## Verification (Worker 3)

### Logic verification outcome

**Rejected.** The new regression test `tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg` (lines 364-373) FAILS under the test runner:

```
$ uv run pytest tests/filters/test_base.py -x -k "lookups"
FAILED tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg
E       Failed: DID NOT RAISE <class 'TypeError'>
```

**Root cause.** Worker 2's `## Fix report` reasons that `**kwargs` is forwarded to `ModelChoiceFilter.__init__` "which raises `TypeError` for unknown kwargs." That premise is false. `django_filters.Filter.__init__` (the MRO base, `.venv/lib/python3.14/site-packages/django_filters/filters.py:79-104`) ends with `self.extra = kwargs; self.extra.setdefault("required", False)` — it silently swallows ALL unknown kwargs into `self.extra`. Confirmed by direct probe with Django settings configured:

```
>>> f = RelatedFilter('ShelfFilter', lookups=['exact', 'in'])
>>> f.extra
{'lookups': ['exact', 'in'], 'empty_label': '---------', 'required': False}
>>> hasattr(f, 'lookups')
False
```

**Behavioral consequence of the fix as shipped.** The artifact's Low #1 framed the goal as "Drop the kwarg and the storage — removes a misleading kwarg from the consumer surface, no-tests-need-touching is the right loud-fail shape." The current diff achieves only half of that: it removes the named parameter and the `self.lookups = lookups or []` line, but the kwarg is now silently absorbed into `self.extra["lookups"]` instead of `self.lookups`. The consumer-facing failure mode is unchanged: `RelatedFilter(BookFilter, lookups=["exact", "in"])` still constructs without error AND still does nothing with the lookups list. The regression test, written to pin the new loud-fail shape, demonstrably proves the fix does not deliver that shape.

**Required next pass (Worker 2 owns).** Choose one:

1. **Add an explicit kwarg rejection in `RelatedFilter.__init__`.** Pop and reject `lookups` from `kwargs` before the `super().__init__` call:
   ```python
   if "lookups" in kwargs:
       raise TypeError(
           "RelatedFilter() got an unexpected keyword argument 'lookups' "
           "(removed from the consumer surface; see spec-027 …)"
       )
   ```
   This honors the artifact's loud-fail premise. The existing regression test then passes verbatim.
2. **Re-scope the regression test to pin the actual new shape** (the kwarg is absorbed into `self.extra` but no longer surfaced via `self.lookups`). If Worker 2 elects this path, the artifact's Low #1 framing ("removes a misleading kwarg from the consumer surface") needs to be revisited — `self.extra["lookups"]` is just as misleading as `self.lookups` was, so this re-scope would be a no-op masquerade and should not be accepted without artifact-level acknowledgement that the loud-fail premise was abandoned.

Recommend option 1 — it matches the artifact's premise and the test Worker 2 already wrote.

**Other diff checks (would have passed if logic verified).**

- Diff scope: matches Low #1 only. Lows #2/#3/#4/#5 untouched as required (forwarded / comment-pass).
- Pre-existing dirty files (`exceptions.py`, `list_field.py`, `scalars.py`, `sets_mixins.py`, `docs/GLOSSARY.md`, etc.) confirmed not touched in this cycle's hunks.
- `grep -rn "RelatedFilter(" django_strawberry_framework/ examples/ tests/` confirms zero call sites pass `lookups=` (only the new regression test does), so removing the named param is non-breaking — the issue is purely that the artifact's loud-fail premise requires an explicit reject, not a passive removal.
- Ruff outcomes (recorded by Worker 2): `uv run ruff format .` pass, `uv run ruff check --fix .` pass.

### DRY findings disposition

Not yet reviewed — logic rejection short-circuits the verification. All three DRY items remain as deferred per the artifact; no action required this pass.

### Temp test verification

No temp tests created. The existing permanent test at `tests/filters/test_base.py:364-373` is the falsification proof for the fix.

### Verification outcome

`revision-needed` — the regression test Worker 2 added falsifies the fix's premise. The kwarg is still silently absorbed by `django_filters.Filter.__init__` into `self.extra`. Worker 2 must add an explicit `TypeError` raise in `RelatedFilter.__init__` (or, less preferred, re-scope the test and the artifact's Low #1 premise).

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/filters/base.py:214-222` — Low #3: converted RST-style double-backticks to single-backticks in the `_decode_and_validate_global_id` docstring so the inline-code convention matches the rest of the file (`TypedFilter`, `ArrayFilter`, `RangeFilter`, `ListFilter`, `_expected_global_id_type_name`, `GlobalIDFilter`, `RelatedFilter`).
- `django_strawberry_framework/filters/base.py:260-272` — Low #3: same RST → single-backtick conversion in the `_GlobalIDMultipleChoiceField` class docstring.
- `django_strawberry_framework/filters/base.py:344-355` — Low #4: extended the `_bind_filterset_owner` citation in `RelatedFilter.bind_filterset`'s silent-no-op contract to name the `_bind_filtersets` umbrella ("subpass 1 of finalizer phase 2.5's `_bind_filtersets` umbrella; H2-rev8 check") so a future reader can trace the cascade without re-grepping the finalizer.
- `django_strawberry_framework/filters/base.py:323-339` — Logic-pass follow-up #3: added a docstring to `RelatedFilter.__init__` describing the new loud-fail behavior. The docstring names the `TypeError` rejection of `lookups=` and explains why the guard runs ahead of `super().__init__` (so `django_filters.Filter.__init__` cannot absorb the kwarg into `self.extra`).

### Per-finding dispositions

- Low #1: implemented in the logic pass (pass 2 `__init__` guard) — comment-pass added the explanatory docstring on top.
- Low #2 (`spec-021` → `spec-027` drift): NOT touched here per dispatch prompt; forwarded to the folder pass `rev-filters.md` for the cross-file sweep.
- Low #3 (backtick convention): applied — single-backtick now consistent across `base.py`.
- Low #4 (`_bind_filterset_owner` umbrella citation): applied.
- Low #5 (GLOSSARY coverage gap for `TypedFilter`-family + GlobalID + mixin symbols): NOT touched here per dispatch prompt; forwarded to project pass `rev-django_strawberry_framework.md`.

### Validation run

- `uv run ruff format .` — pass (183 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)

### Notes for Worker 3

- No `uv.lock` touch; confirmed via `git status` after edits.
- Pre-existing dirty paths untouched per AGENTS.md rule 33 (`exceptions.py`, `list_field.py`, `scalars.py`, `sets_mixins.py`, `docs/GLOSSARY.md`, `docs/feedback.md`, `docs/spec-028-orders-0_0_8.md`, `examples/fakeshop/test_query/test_library_api.py`, `examples/fakeshop/test_query/test_products_api.py`, `tests/filters/test_inputs.py`, `tests/filters/test_sets.py`).
- Only `django_strawberry_framework/filters/base.py` was edited this pass (no source-behavior changes; comment-only).
- No shadow file consulted.
- Lows #2 and #5 deliberately left in place at this file's scope per the artifact's explicit forwarding to folder/project passes.

---

## Changelog disposition

### State

`Warranted but deferred to maintainer`.

### Reason

This cycle ships a consumer-visible loud-fail change at a public-API surface: `RelatedFilter(...)` now raises `TypeError` when a consumer passes `lookups=`, whereas pre-0.0.7 the kwarg was silently absorbed (originally into `self.lookups`, then — between pass 1 and pass 2 — into `django_filters.Filter.__init__`'s `self.extra`). Either way the prior shape was "accepted without effect"; the new shape is "rejected with a typed, named error message." Per `docs/review/worker-2.md` "Changelog dicta — three-state disposition", a typed-error contract change at a public symbol with an actionable error message is a textbook `Warranted but deferred to maintainer` case: the change deserves a release-note entry, but the dispatch prompt did not authorise a `CHANGELOG.md` edit and the package is pre-alpha (`0.0.x`) where `AGENTS.md` rule 32 + START.md "they commit themselves most of the time" reserve the CHANGELOG cadence to the maintainer. `Not warranted` would be wrong (the change is consumer-visible at a public symbol); `Warranted and edited` would be wrong (no plan / maintainer authorisation in the dispatch prompt). The maintainer-ready entry text is preserved verbatim below so it can be lifted at release time without re-derivation.

### What was done

No `CHANGELOG.md` edit. The suggested entry text is preserved verbatim below for the maintainer to lift into the `[Unreleased]` section (it belongs under the existing `### Changed` subsection of `[Unreleased]`, alongside the other `0.0.8` filter-subsystem entries, since `RelatedFilter` itself is in the `0.0.8` ship cohort per the joint-cut deferral pattern documented in spec-027 Decision 10).

### Suggested CHANGELOG entry

```
- `RelatedFilter(...)` now raises `TypeError` when a consumer passes the `lookups=` keyword argument. The kwarg was a verbatim port of the upstream `django-graphene-filters` cookbook shape (`django_graphene_filters/filters.py:120-126`) where it was stored as `self.lookups = lookups or []` but never read by anything in the package — `grep -rn "\.lookups" django_strawberry_framework/ examples/ tests/` finds zero readers, and `grep -rn "lookups=" django_strawberry_framework/ examples/ tests/` finds zero consumer call sites passing it. The previous shape silently accepted the kwarg without honoring or rejecting it, so `RelatedFilter(BookFilter, lookups=["exact", "in"])` produced no lookup expansion AND no error. The new shape raises `TypeError("RelatedFilter does not accept lookups=; the kwarg was removed in 0.0.7 because it had no readers.")` at construction time, ahead of `super().__init__()`, so `django_filters.Filter.__init__`'s `self.extra` cannot silently absorb the kwarg into a different dead-state slot either. No real-world consumer is expected to be affected (no call sites exist in this repository or in any test); consumers who were authoring forward-looking `lookups=` calls in anticipation of upstream behaviour should remove the kwarg. The supported per-relation lookup expansion shape, if it ships, will arrive in a follow-on spec card with a separate name (the `lookups=` name is now reserved as a loud-fail tripwire).
```

### Validation run

- `uv run ruff format .` — pass (183 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)

---

## Iteration log

## Fix report (Worker 2, pass 2)

### Files touched

- `django_strawberry_framework/filters/base.py:323-336` — added an explicit kwarg-rejection guard at the top of `RelatedFilter.__init__` BEFORE `super().__init__()`. If `"lookups"` appears in `kwargs`, the constructor raises `TypeError("`RelatedFilter` does not accept `lookups=`; the kwarg was removed in 0.0.7 because it had no readers.")`. This honors the artifact's loud-fail premise that Worker 3's pass-1 verification flagged was unmet — `django_filters.Filter.__init__` would otherwise silently absorb the kwarg into `self.extra["lookups"]`, leaving the misleading dead-state shape intact under a different name.

### Tests added or updated

- `tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg` — pre-existing from pass 1; now passes under the runner. No edit to the test was needed because the new guard raises the exact `TypeError` the test pinned.

### Validation run

- `uv run ruff format .` — pass (183 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)
- `uv run pytest tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg -x` — **passed** (1 passed in 0.24s; coverage fail-under is a global gate unrelated to the focused-test outcome).

### Notes for Worker 3

- **Why the explicit guard, not a re-scope.** Worker 3's pass-1 verification offered two paths: (1) explicit kwarg rejection or (2) re-scope the test to pin the `self.extra` absorption shape. The dispatch prompt for this pass-2 mandated option 1; this re-pass implements it verbatim. The error message names the kwarg by name and cites the 0.0.7 removal reason ("had no readers") so a consumer who hits it can grep the package and confirm.
- **Guard placement.** Placed BEFORE `super().__init__()` per the dispatch prompt; this ensures the `_has_explicit_queryset` ledger entry is never written when the kwarg is rejected (no partial init state).
- **No other diff scope.** Lows #2/#3/#4/#5 still untouched (forwarded / comment-pass). Pre-existing dirty paths still untouched.
- **No `uv.lock` touch.** Confirmed via `git status` post-edits.
- **No shadow file consulted.** Single-line guard insertion.

## Verification (Worker 3, pass 2)

### Logic verification outcome

**Accepted.** Worker 2's pass-2 fix lands the explicit `TypeError` guard the pass-1 verification required.

1. **Guard placement confirmed.** `django_strawberry_framework/filters/base.py:329-333` contains the explicit `if "lookups" in kwargs: raise TypeError(...)` block, placed BEFORE `super().__init__()` (line 335) and BEFORE the `_has_explicit_queryset` ledger write (line 334). This satisfies the dispatch requirement that no partial-init state can be written when the kwarg is rejected.
2. **Test now passes under the runner.** `uv run pytest tests/filters/test_base.py -x -k "lookups"` reports `1 passed, 42 deselected in 0.24s`. The pass-1 falsification (kwarg silently absorbed into `self.extra["lookups"]`) is now resolved — the explicit guard fires before `django_filters.Filter.__init__` can swallow the kwarg.
3. **Error message quality.** The raised message names the kwarg by name and cites the 0.0.7 removal reason ("had no readers"), so a consumer who hits it can grep the package and confirm the dead-state framing. The `RelatedFilter` symbol is backticked. This matches the artifact's Low #1 loud-fail premise.
4. **Diff scope unchanged.** `git diff -- django_strawberry_framework/filters/base.py tests/filters/test_base.py` shows only the guard insertion + the parameter removal in `base.py` and the regression test addition in `test_base.py`. Lows #2/#3/#4/#5 untouched (forwarded / comment-pass). Pre-existing dirty paths (`exceptions.py`, `list_field.py`, `scalars.py`, `sets_mixins.py`, `docs/GLOSSARY.md`, etc.) confirmed not touched in this cycle's hunks.
5. **Ruff outcomes recorded plausibly.** Worker 2 records `uv run ruff format .` pass (183 files unchanged) and `uv run ruff check --fix .` pass. The diff has no formatting irregularities (trailing comma after the multi-line string args in the `raise TypeError(...)` call honors `AGENTS.md` trailing-comma layout; line length within 100).

### DRY findings disposition

All three DRY items remain as deferred per the artifact (`_typed_method_setter` helper, `EmptyListAwareFilterMethod` base, `_fakes.py` test harness) — no DRY action triggered by the Low #1 fix. Carry-forward per artifact triggers stands.

### Temp test verification

No temp tests created. The permanent test at `tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg` (lines 364-373) is the regression pin and passes under the runner.

### Verification outcome

`logic accepted; awaiting comment pass` — Status flipped to `logic-accepted` at the top of this artifact.

## Verification (Worker 3, pass 3)

### Comment verification outcome

**Accepted.** Worker 2's comment pass lands all three in-scope items from the dispatch prompt; the two forwarded Lows stay untouched as required.

1. **Low #3 backtick consistency at the two named sites.** `git diff -- django_strawberry_framework/filters/base.py` shows the `_decode_and_validate_global_id` docstring (lines 214-221) and the `_GlobalIDMultipleChoiceField` class docstring (lines 261-271) converted from RST-style double-backticks to single-backticks, matching `TypedFilter` / `ArrayFilter` / `RangeFilter` / `ListFilter` siblings. Spot-checked the rendered file — both docstrings now use single-backticks throughout. The artifact's broader observation that `_expected_global_id_type_name` / `RelatedFilter` / `bind_filterset` also carry double-backticks is real but explicitly out of this cycle's dispatch scope (the dispatch prompt scoped item 1 to the two named sites only); flagging as a future-cycle candidate, not a re-spawn trigger.
2. **Low #4 `_bind_filtersets` umbrella citation.** `bind_filterset`'s silent-no-op contract docstring at base.py:361-363 now reads "`types/finalizer.py::_bind_filterset_owner` (subpass 1 of finalizer phase 2.5's `_bind_filtersets` umbrella; H2-rev8 check)" — the umbrella name is named verbatim per the artifact's recommended phrasing. A future reader can now grep `_bind_filtersets` and find the four-subpass entrypoint without re-grepping the finalizer.
3. **New `RelatedFilter.__init__` docstring describes loud-fail.** Lines 329-338 carry the new docstring that names the `TypeError` rejection, cites `lookups=` by name, explains the placement-before-`super().__init__` reasoning (to forestall `django_filters.Filter.__init__`'s `self.extra` absorption), and frames the change as a 0.0.7 removal of a no-readers cookbook artifact. The docstring matches the actual `if "lookups" in kwargs: raise TypeError(...)` body at lines 339-343.
4. **No stale TODOs, no scope creep.** `grep -n "TODO\|FIXME\|XXX"` against `base.py` returns no matches. The diff is scoped to four hunks in `base.py` and zero other paths under `django_strawberry_framework/`. Pre-existing dirty paths from sibling cycles (`exceptions.py`, `list_field.py`, `scalars.py`, `sets_mixins.py`, `docs/GLOSSARY.md`, etc.) are confirmed not touched.
5. **Lows #2 and #5 left untouched at this file's scope.** `spec-021` → `spec-027` drift in `base.py` is unchanged (forwarded to `rev-filters.md` folder pass); GLOSSARY coverage gap for the `TypedFilter`-family + GlobalID + mixin symbols is unchanged (forwarded to `rev-django_strawberry_framework.md` project pass). Both forwards have grep-resolvable triggers in the artifact for the downstream author.
6. **Ruff outcomes.** Worker 3 re-ran `uv run ruff format --check django_strawberry_framework/filters/base.py` (1 file already formatted) and `uv run ruff check django_strawberry_framework/filters/base.py` (All checks passed!). Worker 2's recorded ruff results stand.

### DRY findings disposition

All three DRY items remain as deferred per the artifact (`_typed_method_setter` helper, `EmptyListAwareFilterMethod` base, `_fakes.py` test harness); no DRY action triggered by Low #3 / Low #4 comment edits.

### Temp test verification

No temp tests created or needed for the comment pass.

### Verification outcome

`comments accepted; awaiting changelog disposition` — Status flipped to `comments-accepted` at the top of this artifact.

## Verification (Worker 3, pass 4)

### Changelog verification outcome

**Accepted.** Worker 2's changelog disposition lands `Warranted but deferred to maintainer` with a verbatim maintainer-ready entry, and the framing matches the cycle's actual public-API contract change.

1. **`git diff -- CHANGELOG.md` is empty.** Confirmed — no output, consistent with the "Warranted but deferred" no-edit shape required by `worker-3.md` "Changelog verification job".
2. **`### Suggested CHANGELOG entry` is present and verbatim.** Lines 247-251 carry a complete maintainer-ready paragraph (fenced block) naming the `TypeError`, the kwarg name, the 0.0.7 removal reason, the dead-state cookbook origin (`django_graphene_filters/filters.py:120-126`), the grep evidence for zero readers / zero call sites, the new error message text quoted, and the guidance that the `lookups=` name is now reserved as a loud-fail tripwire. The maintainer can lift this without re-derivation.
3. **"Real consumer-visible change" framing is honest.** `RelatedFilter(...)` is exported through `django_strawberry_framework.filters.__init__` per the artifact's earlier finding; the new shape raises `TypeError` at the public constructor. This is a typed-error contract change at a public-API surface, not an internal-only edit. `Not warranted` would have hidden a real consumer-visible change; `Warranted and edited` would have required dispatch authorisation that the prompt did not give. The chosen state is correct.
4. **Authorisation framing.** The disposition cites the absence of a dispatch authorisation to edit `CHANGELOG.md` AND the pre-alpha cadence reservation per `AGENTS.md` rule 32 + START.md's maintainer-commits framing — both citations are present, not just one.
5. **Section placement guidance.** The disposition notes the entry belongs under `[Unreleased]` `### Changed`, alongside the other `0.0.8` filter-subsystem entries per the joint-cut deferral in spec-027 Decision 10. This is helpful release-day guidance for the maintainer.
6. **Iteration log integrity.** Logic pass (Verification pass 2) and comment pass (Verification pass 3) both recorded interim acceptance; this pass-4 block records terminal acceptance. Append-only history preserved.
7. **Ruff outcomes recorded and re-confirmed.** Worker 2's changelog pass records `uv run ruff format .` pass (183 files unchanged) and `uv run ruff check --fix .` pass. Worker 3 re-ran focused checks on the touched files: `uv run ruff format --check django_strawberry_framework/filters/base.py tests/filters/test_base.py` → "2 files already formatted"; `uv run ruff check django_strawberry_framework/filters/base.py tests/filters/test_base.py` → "All checks passed!".
8. **Diff scope unchanged across the cycle.** `git diff -- django_strawberry_framework/filters/base.py tests/filters/test_base.py` shows the four expected hunks (Low #1 logic guard + parameter removal + docstring; Low #3 backtick conversions at the two named sites; Low #4 `_bind_filtersets` umbrella citation) plus the regression test. Lows #2 and #5 remain forwarded to folder pass and project pass respectively. Pre-existing dirty paths (`exceptions.py`, `list_field.py`, `scalars.py`, `sets_mixins.py`, `docs/GLOSSARY.md`, etc.) untouched by this cycle's hunks.

### DRY findings disposition

All three DRY items remain as artifact-deferred (`_typed_method_setter` helper, `EmptyListAwareFilterMethod` base, `_fakes.py` test harness) with grep-resolvable triggers carried forward to future cycles.

### Temp test verification

No temp tests across the four passes. The permanent regression at `tests/filters/test_base.py::test_related_filter_rejects_lookups_kwarg` (lines 364-373) is the falsification proof and passes under the runner.

### Verification outcome

`cycle accepted; verified` — Status flipped to `verified` at the top of this artifact and the `filters/base.py` checkbox marked complete in `docs/review/review-0_0_7.md`.
