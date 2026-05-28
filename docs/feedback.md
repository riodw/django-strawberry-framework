# Feedback — `docs/spec-021-filters-0_0_8.md` (rev 4)

Rigorous review pass. The spec is exceptionally thorough — four revisions deep, ~1067 lines, with most prior reviewers' load-bearing concerns already addressed. The architectural backbone (six-layer pipeline, `django-filter` as foundation, module-globals materialization for Strawberry's `LazyType.resolve_type`, owner-aware Relay/scalar branch selection, `apply()` as unified resolver-facing classmethod) is sound and the design is internally consistent.

Findings below are organized H (must-fix before implementation), M (coherence / ambiguity), L (nits / structure). I verified several load-bearing claims against the installed packages directly; those are noted inline.

---

## H — must-fix before implementation

### H1 — `DjangoTypeDefinition.related_target_for(field_name)` is referenced 8 times but never specified for addition

The spec leans heavily on `_owner_definition.related_target_for(field_name)` to make the FK/PK conditional in [Decision 4](spec-021-filters-0_0_8.md#decision-4--upstream-primitives-parity-floor) owner-aware (H4 of the prior pass, M6's `GlobalIDFilter` type-name validation, the [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) nested-visibility step, etc.). I verified the current `django_strawberry_framework/types/definition.py` carries no `related_target_for` method — only `consumer_annotated_relation_fields` / `consumer_assigned_relation_fields` frozensets and a single field for the dataclass.

**Slice 3** ([spec-021-filters-0_0_8.md:73-75](spec-021-filters-0_0_8.md)) only adds `filterset_class: type | None = None` to `DjangoTypeDefinition`. **DoD item 7** ([spec-021-filters-0_0_8.md:953](spec-021-filters-0_0_8.md)) only requires that slot. No slice item, no DoD item, and no implementation-plan row contracts adding `related_target_for`. Without it, the owner-aware conditional cannot run — both the runtime filter-instance branch selection in `filter_for_field` AND the Strawberry-`GlobalIDFilter` type-name validation are dead.

**Fix:** Add an explicit task to Slice 3 — grow a `related_target_for(field_name: str) -> DjangoTypeDefinition | None` method (or `(target_type: DjangoTypeDefinition, model_field: Field)` tuple return — whichever the H4/M6 callers actually need) on `DjangoTypeDefinition`, populated at type-creation time from the existing relation-field discovery the definition already runs. Add a matching DoD item. The contract should be: "given a model field name on the owning type, return the related target `DjangoTypeDefinition` if the field is a relation, else `None`." Test under `tests/types/test_definition_order.py` or a new `tests/types/test_definition_relations.py`.

### H2 — `apply()`'s sync/async contract is unspecified; the H1 fix introduces an async dependency without resolving it

Step 3 of [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) derives child visibility querysets via the target `DjangoType.get_queryset(...)`, reusing the existing `_apply_get_queryset_sync` / `_apply_get_queryset_async` dispatch from `relay.py`. But `FilterSet.apply(input_value, queryset, info)` is declared as a single classmethod with a single return shape. If the target's `get_queryset` is async-only (e.g., `aget_queryset`-shaped or returns an awaitable), `apply` cannot synchronously await it — it would have to be itself async, return a coroutine, or detect-and-conditionally-await.

The risk section ([spec-021-filters-0_0_8.md:921](spec-021-filters-0_0_8.md) "Filter applied to a relation that has a custom `get_queryset`") punts this as a fallback ("if a specific composition shape ... breaks under the H1 contract, a follow-up card refactors"). That's not enough — real consumers with async `get_queryset` will hit this on day one of `0.0.8` because the H1 fix is the security-correct path AND the fakeshop tests explicitly seed staff-vs-anonymous flows that would expose any sync/async mismatch.

**Fix:** Pin the contract explicitly. Three viable shapes:
1. **`apply` returns `Awaitable[QuerySet] | QuerySet`**, with internal detection of sync/async `get_queryset`. Caller chooses sync/async resolver. Honest but adds resolver-side branching.
2. **Ship `apply_sync` and `apply_async`** as two methods. Caller picks based on resolver's own sync/async shape. Most explicit, doubles the API surface.
3. **`apply` is `async` always**; sync resolvers await it via Strawberry's sync-bridging. Simplest, requires Strawberry's async path to be available even when the user's schema is otherwise sync.

Recommend option 2 (matching `_apply_get_queryset_sync` / `_apply_get_queryset_async`'s precedent) and document the resolver-side pattern in [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) step 1's example. Update the fakeshop resolver examples (Slice 4) to use the chosen shape.

### H3 — `RangeFilter` form-data key shape is incorrect

[Decision 4](spec-021-filters-0_0_8.md#decision-4--upstream-primitives-parity-floor) M1's converter table ([spec-021-filters-0_0_8.md:482](spec-021-filters-0_0_8.md)) says:

> `RangeFilter` (`range` lookup) | a Strawberry input dataclass `{start: T \| None, end: T \| None}`; runtime emits `from_=..., to=...` as `django-filter` expects

I verified directly: `django_filters.RangeFilter.field` is a `RangeField` (a `forms.MultiValueField`) with two scalar sub-fields. The widget is `RangeWidget` whose `value_from_datadict` reads `name_0` and `name_1` (positional, not named). So `django-filter` expects the form data keys `<name>_0` and `<name>_1`, not `<name>_from` / `<name>_to`. The spec's claim is wrong.

**Fix:** Update the converter table row to specify `<name>_0` / `<name>_1` form-data keys, OR explicitly note the package's `normalize_input_value` constructs a `RangeField`-compatible value (e.g., a 2-tuple or a `slice` — whatever the cookbook does) instead of feeding form-data keys. Verify against the `django-graphene-filters` cookbook's RangeFilter handling and pin the shape literally.

### H4 — Test count drift between [Slice 4 checklist](spec-021-filters-0_0_8.md#slice-checklist) and [Implementation plan table](spec-021-filters-0_0_8.md#implementation-plan)

The spec pins "exactly 13" live HTTP tests in five places (Slice 4 checklist line 79, Test plan line 847, KANBAN body line 898, CHANGELOG body line 905, DoD item 14 line 960). The implementation-plan table at line 787 still says `9` in the "New tests" column for Slice 4. This is a stale value from before rev4 added the four H1/M2/M5/M6 tests.

**Fix:** Change the Slice 4 row's "New tests" cell from `9` to `13`. Also worth scanning the entire table — the line delta (`+260 / -10`) probably needs an upward nudge given four added tests.

### H5 — A `FilterSet` not wired via `Meta.filterset_class` to any `DjangoType` is unmaterializable, but the spec allows resolver-side use via `filter_input_type`

Finalizer phase 2.5 ([spec-021-filters-0_0_8.md:546-552](spec-021-filters-0_0_8.md)) iterates `DjangoType`s with `definition.filterset_class is not None` and materializes their input classes. The `filter_input_type(MyFilter)` helper ([Decision 11](spec-021-filters-0_0_8.md#decision-11--filter_input_typefilterset-consumer-helper)) takes a `FilterSet` directly, with no `DjangoType` link. A consumer who declares:

```python
class StandaloneFilter(FilterSet):
    class Meta:
        model = Book
        fields = {...}

@strawberry.field
def my_resolver(self, filter: filter_input_type(StandaloneFilter) | None = None) -> list[BookType]: ...
```

but never writes `Meta.filterset_class = StandaloneFilter` on `BookType` will get a `KeyError` from `LazyType.resolve_type` at `strawberry.Schema(...)` time — the input class was never materialized.

This is more than an edge case. The user-facing API example ([spec-021-filters-0_0_8.md:241-275](spec-021-filters-0_0_8.md)) shows GalaxyType wiring `Meta.filterset_class = filters.GalaxyFilter`, but the spec doesn't make this wiring mandatory for any FilterSet that's referenced from a resolver — it's implicit. A consumer who wants per-resolver filtering without per-type wiring (e.g., the same filter exposed on two unrelated root resolvers, or a one-off filter that isn't owned by a single type) will trip over this.

**Fix:** Choose one:
1. **Materialize on first `filter_input_type(MyFilter)` call** — the helper records the FilterSet in a "pending materialization" set, and the finalizer iterates BOTH `Meta.filterset_class`-wired filtersets AND helper-referenced ones.
2. **Validate at finalize that every `filter_input_type`-referenced FilterSet is also Meta-wired** — fail loud with a `ConfigurationError` naming the orphan filterset and the resolver(s) that reference it.
3. **State explicitly that `Meta.filterset_class` is the only path** — and add a `ConfigurationError` at `filter_input_type` call time when the FilterSet isn't already wired (requires the helper to do registry lookups at call time, which is doable since `filter_input_type` already runs eager validation).

Option 1 is the most generous. Option 2 is the most consistent with the package's "fail-loud at finalize" pattern. Either way, pick one and pin it in [Decision 11](spec-021-filters-0_0_8.md#decision-11--filter_input_typefilterset-consumer-helper) + DoD.

### H6 — "Security/scope boundary" wording for `RelatedFilter(queryset=...)` is inconsistent with M4's active-branch-only application

The user-facing API example at [spec-021-filters-0_0_8.md:213-220](spec-021-filters-0_0_8.md) describes `RelatedFilter(queryset=...)`:

> Explicit queryset acts as a security/scope boundary: nested filters can narrow it but cannot escape "public galaxies only".

But M4 narrows the rule: the constraint applies only when the related branch is active in the normalized input ([spec-021-filters-0_0_8.md:604, 800](spec-021-filters-0_0_8.md)). So `filter: {}` or `filter: { name: { iContains: "..." } }` — both with the `galaxy` branch absent — return the unconstrained parent queryset, including parents whose `galaxy.is_private == True`.

That's not a security boundary; it's a "scope when you filter through this relation" semantic. A naive consumer reading "security boundary" will assume the constraint always applies, ship a feature where private galaxies are surfaced to anonymous users, and discover the leak in prod.

**Fix:** Either (a) rename "security/scope boundary" to "filter-scope constraint" / "filter-target constraint" everywhere it appears, dropping the security framing; OR (b) reconsider whether M4's active-branch refinement is the right default — making it always-on preserves the security guarantee at the cost of "row loss the consumer never asked for" (which the spec's M4 justification correctly identifies as a real downside, but the security guarantee may be more important to default to). Recommend (a) — keep M4, drop the "security" framing in the docstring example, and explicitly note in [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) that visibility (= security) is the job of `get_queryset`, not `RelatedFilter(queryset=...)`.

---

## M — coherence / ambiguity

### M1 — `apply()`'s internal pipeline is described as 8 sequential steps but the spec doesn't decompose it into sub-helpers

[Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) lists steps 1–9 (resolver-side + apply-internal). Apply alone owns: input normalization, lookup-name mapping, related-filter visibility derivation, request extraction, instantiation, `check_permissions`, explicit `form.is_valid`, constraint application, `.qs` return. That's a 100+ line method by any reasonable budget. The factories module was carefully decomposed (`_build_logic_fields`, `_build_input_fields`, `convert_filter_to_input_annotation`, `normalize_input_value`, `materialize_input_class`); `apply` deserves the same treatment.

**Fix:** Add a recommended internal decomposition to [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) — e.g., `_normalize_input` (Strawberry → form-data), `_derive_related_visibility_querysets` (step 3, the H1 work), `_run_permission_checks`, `_validate_form_or_raise` (the M2 work), `_apply_related_constraints` (the M4 work). Pin signatures so test coverage can target each step. Without this, every implementer reinvents the decomposition and tests miss seams.

### M2 — `check_permissions` scope is unstated: active-input-only or all-declared?

[Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) step 5 says `cls.check_permissions(input_value, request)` "recurses through `RelatedFilter`s into child filtersets' `check_*_permission` methods." But the spec doesn't pin whether per-field `check_<field>_permission(request)` runs for:
- **(a) every declared field** regardless of whether the field appears in the input, OR
- **(b) only fields present in the input.**

The cookbook's `AdvancedFilterSet.check_permissions(request)` (no input arg) walks declared filters and runs every `check_*_permission`. The package's version takes `input_value` and could reasonably restrict to active branches. The behavior difference is material: under (a), a consumer who declares `check_name_permission` but the request lacks the `name` filter still gets the check run (and potentially raises); under (b), the check only fires when the consumer's query actually references `name`.

**Fix:** Pin which shape, with reasoning. Option (b) is the more obvious user mental model ("permissions gate use of the filter, not its declaration"), but it diverges from the cookbook. Either is defensible — just state it.

### M3 — DoD numbering has "6a" — symptom of a post-hoc insertion

DoD goes 1, 2, 3, 4, 5, 6, **6a**, 7, 8 ... 26. Item 6a ([spec-021-filters-0_0_8.md:952](spec-021-filters-0_0_8.md)) covers `filter_input_type` re-export, which is a real DoD item and not subordinate to item 6. Renumber to make it item 7 and shift everything down by 1.

### M4 — `Annotated[name_variable, ...]` shape is unverified for the helper's intended use

`filter_input_type` returns `Annotated[name, strawberry.lazy(...)]` where `name` is a runtime string variable (`f"{filterset_class.__name__}InputType"`). I verified directly that Python's typing accepts this (the string becomes a `ForwardRef` in `__args__[0]`). The spec relies on this and the L3 future-annotations test pins the helper's behavior end-to-end, but it doesn't have a unit test that asserts the `Annotated[name_variable, ...]` shape produces a `ForwardRef`-wrapped first arg. Add a small unit test in `test_inputs.py` (`test_filter_input_type_returns_forwardref_in_annotation_args`) that asserts `result.__args__[0]` is a `ForwardRef` with `__forward_arg__ == "MyFilterInputType"`. Catches any future Python typing regression.

### M5 — Choice-enum runtime `.value` assumption needs to be pinned to a Strawberry-enum convention

The converter table ([spec-021-filters-0_0_8.md:479](spec-021-filters-0_0_8.md)) says `ChoiceFilter` / `TypedChoiceFilter` map to a Strawberry `Enum` member; runtime normalizes via `enum_member.value`. This is true when the Strawberry enum wraps a Django `TextChoices` / `IntegerChoices` where `.value` is the DB value. It is NOT necessarily true for hand-rolled `strawberry.enum`-decorated Python enums. The package likely already auto-generates Strawberry enums from Django choices via the existing `types/converters.py` pipeline, so the assumption holds — but the spec should cite the converter pipeline (or pin that `convert_filter_to_input_annotation` only handles `Choices`-derived enums, raising `ConfigurationError` for anything else).

### M6 — L3 future-annotations description is approximate; tighten

[Decision 11](spec-021-filters-0_0_8.md#decision-11--filter_input_typefilterset-consumer-helper) ([spec-021-filters-0_0_8.md:743](spec-021-filters-0_0_8.md)) says with `from __future__ import annotations`, "Python stores the expression as a string and Strawberry evaluates it lazily during type/field processing." More precisely: under PEP 563 / future-annotations, Python stores the ENTIRE annotation (`filter_input_type(GalaxyFilter) | None`) as a string. Strawberry resolves this string by calling `typing.get_type_hints(resolver, ...)` (or equivalent) at type-collection time, which evaluates the string in the resolver's function `__globals__`. THAT call evaluates `filter_input_type(GalaxyFilter)` — invokes the helper, runs validation, returns `Annotated[...]`. So validation does run; it runs at type-processing time, not module-load time.

Two implications worth pinning:
1. Under future-annotations, `GalaxyFilter` must be present in the resolver's module globals at type-processing time (not just at module-load).
2. Strawberry may evaluate the annotation more than once during a single schema build (the spec says this once at L3 but the test plan's `test_filter_input_type_under_future_annotations` doesn't pin idempotency under repeated evaluation). Worth asserting `filter_input_type` is safe to call repeatedly with the same FilterSet — it currently is, but no test pins this contract.

### M7 — `GraphQLError` import path is unspecified

The spec uses `GraphQLError` throughout (M2's `"Invalid filter input"`, M6's `"GlobalID type mismatch"`, the per-field permission gate example) without specifying whether it's `graphql.GraphQLError` or `strawberry.exceptions`. Strawberry resolvers conventionally raise `graphql.GraphQLError` (the one Strawberry's response builder honors for the `extensions` payload). Pin this once in [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) and stop guessing per-site.

### M8 — `info.context.request` vs `info.context` dual-shape extraction is fragile

Decision 8 step 4 ([spec-021-filters-0_0_8.md:601](spec-021-filters-0_0_8.md)) says apply "extracts `request = info.context.request` (or `info.context` directly when the consumer's request adapter does not wrap it)." Dual-shape extraction is a footgun — different consumers will get different behavior based on whatever the local `info.context` happens to look like. The package is Django-shaped; pin one canonical shape (almost certainly `info.context.request`, since that's the Strawberry-Django convention) and require consumers to conform. If the package supports a wrapper-less `info.context = HttpRequest` shape today, document that as the alternate path and have apply detect it with a single isinstance check.

### M9 — Performance risk for `Meta.fields = "__all__"` is understated

The risk section ([spec-021-filters-0_0_8.md:923](spec-021-filters-0_0_8.md)) frames this as O(field_count × lookup_count) at finalize time, "cached." But the produced input type's SDL grows linearly with that product. A 30-field model × ~8 default lookups = 240 input fields. Two such types on a schema = 480 fields. Apollo/GraphiQL introspection responses inflate; client codegen tools get slow. The risk is not just finalize-time CPU — it's the wire format. Worth bolstering: "consumers using `__all__` on wide models should expect noticeable schema-size growth; the workaround is to declare an explicit `Meta.fields` dict with narrower lookup sets."

### M10 — `extensions.errors` serialization shape relies on `forms.utils.ErrorDict.get_json_data()`

[Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) step 6 says `extensions.errors` is `filterset.errors` "rendered through `forms.utils.ErrorDict.get_json_data()` so each field's error list is JSON-serializable." Verify this method exists in the package's supported Django range (`>=5.0`?) — `get_json_data` has been around for a while but it's worth pinning the Django-version dependency in the risk section. Also worth pinning the structure consumers can expect: `{field_name: [{"message": ..., "code": ...}, ...]}` per the Django form contract.

---

## L — nits / structure

### L1 — Spec length (~1067 lines) impedes review

The four-revision history alone is ~25 lines and tells future readers about the spec-evolution process rather than the spec itself. Slice 5's KANBAN past-tense body ([spec-021-filters-0_0_8.md:898](spec-021-filters-0_0_8.md)) is a single ~1500-word paragraph that's effectively unreadable. Consider:

1. Moving rev history to a separate `docs/spec-021-filters-0_0_8-history.md` companion (or just deleting it once the spec is "settled" — the git log preserves the rev arc).
2. Breaking the KANBAN body into bullets; the past-tense Done body is going to be consumed by humans scanning Done columns, not by anyone reading it as flowing prose.

### L2 — Many `per H1 of `docs/feedback.md`` references will dead-link once feedback is wiped between reviews

The spec body cites `H1 / H2 / H3 / H4 / M1 / M2 / M3 / M4 / M5 / M6 / L1 / L2 / L3 / L4` of `docs/feedback.md` ~60+ times across the body. Once feedback.md is wiped (as it is now for this review), those anchors point at nothing. The corrections have been folded into the spec, so the references serve only to credit the source of each change. Consider:

1. Strip the `per X of feedback.md` annotations once a revision is finalized — the spec content already says what it needs to say.
2. OR keep them but understand they're for audit only; future readers will skip them.

### L3 — Two example domains (Galaxy/CelestialBody for user-facing API, Branch/Shelf for fakeshop tests)

The user-facing API section ([spec-021-filters-0_0_8.md:194-228](spec-021-filters-0_0_8.md)) uses Galaxy/CelestialBody. Slice 4 / fakeshop uses Branch/Shelf/Book. The two domains have no mapping. A reader following the spec from API examples to test plan has to context-switch. Pick fakeshop (since that's where tests actually live) and rewrite the API examples to use Branch/Shelf.

### L4 — Venv paths as first-class links

Line 113 (`/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/`) and similar are useful for the spec author but won't resolve for anyone else, ever. Inline these as "upstream package, currently installed at <path> on the maintainer's machine" or convert them to PyPI package + relative-path references that work from any checkout.

### L5 — Joint-`0.0.8` cut posture: spec assumes this card doesn't ship last

DoD item 23 says "version bump is NOT in this card" but [Decision 10](spec-021-filters-0_0_8.md#decision-10--joint-008-cut) says "owned by whichever card ships last in the bundle." If 021 ships last (e.g., 022 and 023 land first), DoD item 23 contradicts the actual responsibility. Either:
1. Add a contingency clause: "if 021 is the last card to merge in the `0.0.8` cohort, item 23 is replaced by 'this card owns the bump.'"
2. Or, more cleanly, factor the version bump out of all three cards entirely and ship it as a dedicated tiny "0.0.8 cut" card.

### L6 — `filter_queryset` vs `apply` distinction is helpful but could be clearer at the top of [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation)

The spec carefully separates `apply(input_value, queryset, info)` (resolver-facing) from `filter_queryset(self, queryset)` (django-filter override for tree-form logic). This is the right design — but it lands deep in [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) step 8 and in Decision 11's prose. A reader scanning the spec would benefit from a single-line statement at the top of the User-facing API: "Consumers call `FilterSet.apply(...)` from resolvers; the django-filter `filter_queryset` instance method is an internal override and not the consumer surface."

### L7 — `Annotated[name, ...]` works with a string variable, but worth a comment in the helper

The helper body uses `Annotated[name, strawberry.lazy(...)]` where `name` is a runtime-computed string. I verified this works (Python's typing wraps the variable string as `ForwardRef`). It's subtle enough that the helper deserves a one-line code comment confirming the behavior so future maintainers don't refactor it into something that breaks the lazy-resolution.

---

## What's strong (worth keeping)

- The four-revision arc has tightened the spec without bloating it. Most prior-pass corrections (H1/H2/H3/H4/M1-M6 from rev3) are landed cleanly and the prose remains internally coherent.
- The `LazyType.resolve_type` reading `module.__dict__` correction (H1 of an earlier pass) is verified directly against the installed Strawberry and the spec's design hangs together on that verification.
- The owner-aware FK/PK conditional (H4) is the right shape for multi-`DjangoType`-per-model schemas — the alternative (model-keyed lookup) would have shipped a real wire-shape bug.
- The active-branch refinement (M4) is the right call for filter ergonomics even though it requires the H6 docstring fix.
- The explicit `form.is_valid()` call (M2) closes a real silent-degradation in `BaseFilterSet.qs`.
- Slice 6 being deferred until the sibling ordering card ships is the right call.
- The 13-test fakeshop coverage exercises the actual GraphQL surface — Relay vs scalar split, visibility scoping, form validation, GlobalID type validation, cross-module lazy resolution. That's a meaningful coverage floor.

## Suggested order of operations for the implementer

Given the H-level findings, the spec needs another small revision before implementation begins. Recommended sequence:

1. **Address H1, H3, H4 mechanically** — they're isolated text fixes.
2. **Pin H2** (sync/async) with a short decision section explaining the chosen shape and its consumer impact. Recommend going with `apply_sync` / `apply_async` for explicitness.
3. **Pin H5** (orphan FilterSet lifecycle) — choose option 2 (validate at finalize) for the smallest API surface.
4. **Reword H6** — drop the "security boundary" framing in the user-facing example and make the contract narrower.
5. M-level findings can fold into the rev5 pass or be deferred to implementation review.
6. L-level findings can stay open through rev5 — they're polish.

After those fixes, the spec is implementation-ready.
