# Review: `django_strawberry_framework/filters/inputs.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: `_normalize_range_value`'s dual `dict` / object accessor pair.** `inputs.py:534-541` reads `start` / `end` twice with the same `isinstance(raw_value, dict)` discriminator inlined per axis. The two reads share the same shape (single discriminator, single attr name, single fallback). Defer until a third positional-key Range axis lands (`step`, `bucket`, etc.) OR a second filter primitive grows the same dataclass-or-dict input pattern — then fold both axes through a `_attr_or_key(raw_value, "start", default=None)` helper local to this module. Single-axis pair below threshold today; the named-constant flip is not worth the extra indirection.
- **Defer-with-trigger: `_owner_type_name(owner_definition) or "Filter"` fallback for the GraphQL type name passed to `_choice_enum_from_filter`.** Two sites — `inputs.py:319` (`_element_annotation`) and `inputs.py:377` (`convert_filter_to_input_annotation`'s `ChoiceFilter` branch) — repeat the same `_owner_type_name(...) or "Filter"` expression. Defer until a third call site lands OR the literal `"Filter"` fallback gains semantic distinction (e.g. ChoiceFilter vs ListFilter want different default type-name suffixes). Today the dispatch goes through the same `_choice_enum_from_filter(filter_instance, type_name, model_field)` signature, so the read-cost of the inline duplicate is one line; a `_choice_enum_type_name(owner_definition)` wrapper would be a one-line helper feeding a one-line helper.
- **Defer-with-trigger: `list[_element_annotation(filter_instance, model_field, owner_definition)]` repeats three times verbatim.** Sites: `inputs.py:368` (`BaseCSVFilter` branch), `inputs.py:373` (`(ListFilter, ArrayFilter)` branch). Plus the singular `_element_annotation(...)` is also called on `inputs.py:375` and `inputs.py:396`. Defer until a fourth list-shaped filter primitive lands (e.g. a future `TupleFilter` / `JSONArrayFilter`); fold the three list-of-element call sites through a `_list_element_annotation(filter_instance, model_field, owner_definition) -> list[T]` helper at that point. Today the branch-discrimination is the dispatch — three short sites are easier to read than a helper indirection.
- **Defer-with-trigger: `_pascal_case(field_name)` + the immediate `{}RangeInputType` suffix derivation in `_build_range_input_class` (`inputs.py:510`).** Same shape as `_input_type_name_for` (delegates to `FilterSet.type_name_for` for the root `{cls.__name__}InputType` derivation) but the `RangeInputType` per-field suffix derives a different naming family ("type name OF a single range-shaped field within an input"). Defer until a second per-field input-type family lands (e.g. a `ListInputType` for `ListFilter`-shaped inputs whose name needs distinct collision protection from the operator-bag class name), then promote to `FilterSet.type_name_for(field_path, kind=...)` or a dedicated `_field_input_type_name(field_name, kind)` helper. Today only `_build_range_input_class` needs the field-keyed naming family.

## High:

None.

## Medium:

### `_build_input_fields`'s top-level grouping passes the raw `top_name` through `python_attr = top_name.replace("__", "_")` without re-validating against `_pascal_case`'s "no word characters" guard

Issue: `inputs.py:688` (`python_attr = top_name.replace("__", "_")`) and `inputs.py:712` (`bag_name = filterset_cls.type_name_for(python_attr)`). `_pascal_case` raises `ConfigurationError` for inputs with no word tokens (`""`, `"_"`, `"__"`, `"___"`) per `inputs.py:174-179`, and this raise is reached **only** through `_build_range_input_class` (which `_pascal_case(field_name)`s) or through `FilterSet.type_name_for(field_path)` (which `pascal_case(part)`s each `__`-split segment). A `top_name` of `"__"` (i.e. a declared filter literally named `__` on a `FilterSet`) would `.replace("__", "_") -> "_"`, then `type_name_for("_")` would call `pascal_case("_")` via `sets_mixins.py:65` which yields `""`, so the bag class name is `f"{cls.__name__}{}{_field_type_suffix}"` = `f"{cls.__name__}InputType"` — colliding with the root input class name silently. The downstream `_pascal_case` guard never fires because this branch never reaches `_pascal_case`.

Why it matters: this collision is exactly the failure mode `_pascal_case`'s `ConfigurationError` was raised to guard against (collision against a generic `"FilterInputType"`) — but the guard is at the wrong layer. The leaf-path branch produces a colliding bag class via the `type_name_for(field_path)` path, which bypasses `_pascal_case` and lands directly at the `pascal_case` helper from `utils.strings`. A real-world `top_name = "__"` is unlikely (a user would have to declare a `Filter()` class attribute named literally `__`), but the silent-collision path is the load-bearing concern: the guard's docstring explicitly says it's there to prevent "a generic ``FilterInputType``" — the leaf branch can still produce one.

Recommended change: route both layers through the same name-validation helper. Either (a) have `FilterSet.type_name_for(field_path)` call `_pascal_case` on each `field_path` part and surface `ConfigurationError` for empty results (the canonical fix — fixes the guard once and protects all callers), or (b) call `_pascal_case` on `python_attr` defensively in `_build_input_fields` before passing to `type_name_for`. Option (a) is the higher-quality fix; option (b) is a local patch that leaves `sets_mixins.py::type_name_for` still callable with no-word-character input from a future caller. A regression test: declare a `FilterSet` with a filter attribute named `"__"` and assert `ConfigurationError` is raised before any `strawberry.input(...)` decoration runs.

```django_strawberry_framework/filters/inputs.py:688-712
        python_attr = top_name.replace("__", "_")
        graphql_name = _camel_case(python_attr)
        ...
        # Leaf path: build a per-field operator-bag input class.
        sample_filter = next(iter(lookup_bag.values()))
        bag_name = filterset_cls.type_name_for(python_attr)
```

### `_normalize_range_value` returns positional keys with `None` values when `raw_value` is a dataclass-style object with missing axes

Issue: `inputs.py:519-542`. `_normalize_range_value` always returns both `{base}_0` and `{base}_1` keys, defaulting to `None` for either axis via `getattr(raw_value, "start", None)` / `getattr(raw_value, "end", None)`. The dict branch via `raw_value.get("start")` likewise defaults to `None` for a missing key. Django's `RangeWidget.value_from_datadict` interprets a `None` form-data value as "field not supplied" and Django-filter then short-circuits the filter — so the `None` values pass through. BUT: the consumer-facing contract for `_normalize_range_value` is "the positional form-data patch", and inserting `{<name>_0: None, <name>_1: None}` into `django-filter`'s form-data dict surfaces `None` instead of "unset" to any caller that walks `data.keys()`. The current `FilterSet._normalize_input` caller merges the patch unconditionally, which is fine for `django-filter` — but a future caller that inspects the patch's keys (e.g. logging, audit, debug-only path coverage) gets a misleading "both axes supplied" signal.

Why it matters: this is a contract-vs-implementation mismatch, not a wrong-data bug — `django-filter` does the right thing with the `None`-valued keys today. But the docstring (`"the positional form-data patch ``{<name>_0, <name>_1}``"`) frames the return shape as "what django-filter consumes" without qualifying "with `None` for missing axes". Tests cover the both-axes-supplied path (`test_normalize_input_value_range_filter_emits_positional_keys`) but not the one-axis-only path. A `RangeFilter` against a `start=5, end=None` input should normalize to `{lifetime_fines_cents_0: 5}` (one key) per the form-data convention django-filter expects for partial ranges; emitting `{lifetime_fines_cents_0: 5, lifetime_fines_cents_1: None}` works for now but cements a divergent shape if a future consumer reads it as "both axes set, one is None" vs "only start was supplied".

Recommended change: drop axes whose value is `None`. Replace the unconditional `return {f"{base}_0": start, f"{base}_1": end}` with a comprehension that skips `None`s:
```
patch: dict[str, Any] = {}
if start is not None:
    patch[f"{base}_0"] = start
if end is not None:
    patch[f"{base}_1"] = end
return patch
```
Pair with a regression test that pins a partial-range input (only `start`) emits a single-key patch. The all-supplied path stays correct; the partial-range path stops surfacing `None` to the form-data dict. Same explicit-`is not None` rigor as `normalize_input_value`'s `raw_value is None or raw_value is UNSET` guard (`inputs.py:434`).

### `_unwrap_enum_member` is structurally correct but the iteration shape in `normalize_input_value`'s `BaseCSVFilter` / `ListFilter` branches assumes `raw_value` is non-`None` iterable

Issue: `inputs.py:444` (`[_unwrap_enum_member(item) for item in raw_value]` inside the `BaseCSVFilter` branch) and `inputs.py:450` (same pattern under `(ListFilter, ArrayFilter)`). The `raw_value is None or raw_value is UNSET` short-circuit at `inputs.py:434` correctly defends against `None` / `UNSET`, so list iteration on `raw_value` is safe in those branches.

However, the `GlobalIDMultipleChoiceFilter` branch at `inputs.py:438` does `[_encode_global_id_input(item) for item in raw_value]` — same iteration assumption, same safety guarantee. The pattern is consistent. **But:** a `raw_value` that is `[]` (an empty list — a legitimate "filter by no globalIDs" input) reaches the comprehension and yields `[]`, which `GlobalIDMultipleChoiceFilter.filter` then evaluates against. The downstream `base.py::GlobalIDMultipleChoiceFilter.filter` documents the empty-list contract; that path is intentional. **Same for `BaseCSVFilter`'s empty-CSV input.**

Why it matters: this is a no-defect-but-worth-recording observation — the empty-list pass-through to `django-filter` is a documented part of the contract per the test pin at `test_normalize_input_value_global_id_list`. The Medium I'd surface is a different concern: `_unwrap_enum_member`'s structural `isinstance(value, enum.Enum)` check (`inputs.py:493`) is good for member detection, but the iteration in the `ListFilter` branch doesn't recurse into nested containers. A `list[list[Color.RED]]`-shaped input (nested-list `ArrayField` lookup, not currently supported but a foreseeable shape) would pass enum members unmodified inside the inner list. Today no `ListFilter`-shaped Django field maps to a nested-list scalar via the converter pipeline, so the case is unreachable from a real Django field.

Recommended change: downgrade this from Medium to a documentation note. Add a one-line comment at `inputs.py:444` / `inputs.py:450` flagging the assumption ("one-level unwrap — nested-list / nested-dict inputs unsupported by this code path; the Django converter pipeline does not produce such shapes today"). Pair with a regression test only if a nested-shape `ListFilter` lands in a future spec.

After consideration: this is actually a Low (documentation only), not Medium. **Demoting to Low #4 below.** Keeping the Medium heading present and writing `None.` after the two Mediums above.

Actually, recategorizing: the iteration safety observation above doesn't have a real defect today, so removing it from Medium entirely and **NOT** including it as a Low either (per the artifact-template rule "Do not include speculative defects"). The two Mediums above stand.

## Low:

### Stale `spec-021` citation anchors throughout the module (forwarded — do not re-file here)

Per the dispatch prompt, the `spec-021` → `spec-027` citation drift across the entire `filters/` subpackage is already forwarded to the folder pass via `rev-filters__base.md::Low #2`'s subpackage-wide forward to `rev-filters.md`. Sites in this file: `inputs.py:6`, `inputs.py:57`, `inputs.py:66`, `inputs.py:124`, `inputs.py:144`, `inputs.py:192`, `inputs.py:236`, `inputs.py:270`, `inputs.py:382`, `inputs.py:467`, `inputs.py:526`, `inputs.py:808`, `inputs.py:819` (13 hits). The folder pass `rev-filters.md` is the right place for the cross-file sweep — per the worker-1 memory carry-forward from `rev-filters__base.md` and `rev-filters__factories.md`, sweeping one file in isolation would create internal inconsistency. Reference only; no in-cycle edit here.

### "Slice 1 / Slice 2 / Slice 3" tense-rot in module + helper docstrings

Sites: `inputs.py:6-15` (module docstring "Slice 1 landed ..., Slice 2 adds ..., Slice 3 lands ..."), `inputs.py:70-74` (LOOKUP_NAME_MAP comment "Slice 1 consumes ..., Slice 2 consumes ..."), `inputs.py:121-125` (`FieldSpec` docstring "Slice 3's `materialize_input_class`"), `inputs.py:145-150` (`_materialized_names` comment "Slice 3's ``materialize_input_class``"), `inputs.py:794-797` (`construct_search` docstring "Spec sub-bullet 4 for Slice 2 lands the helper now even though the `Meta.search_fields` card is ``0.1.2``"). Per active plan, this is a `0.0.7` release; Slice 2 and Slice 3 are both shipped (Slice 3 added `materialize_input_class` + `clear_filter_input_namespace`, both present in source today — `inputs.py:812` and `inputs.py:846`). The "Slice 2 adds" / "Slice 3 lands" present-tense framing reads as in-flight design intent for a future reader, not as audit-trail.

Why it matters: same severity calibration as the `list_field.py` `spec-016` → `spec-020` citation drift and the `scalars.py` `TODO-ALPHA-028` → `TODO-ALPHA-035-0.0.11` anchor drift — the policy text is itself correct against the spec; only the tense rotated. Worker 1 memory carry-forward from `factories.py`: "audit every `Slice N's finalizer ...` docstring claim for tense rot — Slice 3 is shipped at 0.0.7 per the active plan".

Recommended change: comment-pass edits to soften tense. Module docstring should read "Slice 1 landed ..., Slice 2 landed ..., Slice 3 landed ..." (consistent past-tense for shipped slices). The LOOKUP_NAME_MAP comment should drop the "Slice 1 consumes ... / Slice 2 consumes ..." per-slice attribution in favor of "Consumed by `FilterSet._normalize_input`, `_build_input_fields`, and `normalize_input_value`" (concrete site references). Same shape for the `FieldSpec` docstring and `_materialized_names` comment. The `construct_search` "Slice 2 lands the helper now" doc-stamp should soften to "Lands now even though the `Meta.search_fields` card is deferred" since "Slice 2" no longer disambiguates against any future slice. Pair the rewrites with a sweep for "Slice N" tokens across the file (13+ hits).

### `_pascal_case`'s `ConfigurationError` mentions "rename the filter / field" but the helper has three Django-filter-aware callers and one form-key caller

Site: `inputs.py:175-179`. The error message:
```
f"_pascal_case received {name!r} which contains no word "
"characters; rename the filter / field so its name has at "
"least one alphanumeric token."
```

Callers: `_input_type_name_for` (`inputs.py:195` — calls `filterset_class.type_name_for()` which calls `pascal_case` per part), `_build_range_input_class` (`inputs.py:510` — calls `_pascal_case(field_name)` directly with the filter's `field_name`), and indirectly via every `_build_input_fields` operator-bag class name (`inputs.py:712` — calls `type_name_for(python_attr)` which calls `pascal_case(part)` from `utils.strings`, not `inputs._pascal_case`).

The only direct `inputs._pascal_case` consumer that surfaces this error today is `_build_range_input_class`. The "rename the filter / field" guidance is correct for that single direct consumer (the filter's `field_name`). The indirect callers (`_input_type_name_for`, `_build_input_fields`'s bag-class naming) route through `sets_mixins.py::type_name_for` -> `utils.strings.pascal_case` -> no error, so they cannot trip this `_pascal_case` guard.

Why it matters: the error message reads as if `_pascal_case` is reached from multiple consumer paths and the user must reason about which "filter / field" to rename — but only one consumer (the `RangeFilter`'s `field_name`) reaches this guard today. The error is correctly raising, just not naming the surfacing path. Same severity as `_camel_case`'s docstring claim that it handles the empty-string case (it does, at `inputs.py:757`) — citation precision, not a logic defect.

Recommended change: comment-pass edit. Tighten the error message to name the immediate consumer: `"rename the RangeFilter's `field_name=` so its name has at least one alphanumeric token."` Pair with a Low-impact note in the docstring naming the one direct consumer. Alternatively, leave the message as-is and add a docstring sentence: `"Direct callers: \`_build_range_input_class\` (others route through \`sets_mixins.py::type_name_for\`)."` so a future reader knows the error never fires from the operator-bag class naming path.

### `_unwrap_enum_member` one-level unwrap shape is undocumented

Site: `inputs.py:444` and `inputs.py:450`. The `BaseCSVFilter` and `(ListFilter, ArrayFilter)` branches do `[_unwrap_enum_member(item) for item in raw_value]` — a single-level unwrap. A nested `list[list[Color.RED]]`-shaped input would not recursively unwrap. The Django-filter converter pipeline does not produce such shapes today; no real consumer hits this case. But the helper's docstring (`inputs.py:483-492`) doesn't mention the iteration depth — a future caller adding a nested-shape `ListFilter` could miss the limit.

Why it matters: same severity as the `_pascal_case` direct-vs-indirect caller calibration — documentation precision for a one-level-deep helper that may be called from a deeper shape in a future spec.

Recommended change: add one line to the docstring at `inputs.py:483-492`: `"Single-level unwrap — nested-list / nested-dict inputs are not recursively unwrapped (no current consumer produces such shapes)."` No code change needed today.

### GLOSSARY coverage gap for `LOOKUP_NAME_MAP`, `LOOKUP_PREFIXES`, `convert_filter_to_input_annotation`, `normalize_input_value`, `construct_search`, `INPUTS_MODULE_PATH`, `FieldSpec`, `build_input_class`, `materialize_input_class`, `clear_filter_input_namespace`, `_field_specs`, `_materialized_names`, `HIDE_FLAT_FILTERS`

GLOSSARY drift quick-check: per the dispatch's required-grep set — `filter_input_type`, `convert_filter_to_input_annotation`, `normalize_input_value`, `LOOKUP_NAME_MAP`, `LOOKUP_PREFIXES`, `construct_search` — only `filter_input_type` has a GLOSSARY entry (`docs/GLOSSARY.md:436-460`). The other five required-grep symbols are ABSENT.

Sites: `inputs.py:53` (`INPUTS_MODULE_PATH`), `inputs.py:58-63` (`LOOKUP_PREFIXES`), `inputs.py:75-102` (`LOOKUP_NAME_MAP`), `inputs.py:117-130` (`FieldSpec`), `inputs.py:336-400` (`convert_filter_to_input_annotation`), `inputs.py:403-451` (`normalize_input_value`), `inputs.py:561-592` (`build_input_class`), `inputs.py:676` (`HIDE_FLAT_FILTERS` settings key — undocumented in GLOSSARY), `inputs.py:791-804` (`construct_search`), `inputs.py:812-843` (`materialize_input_class`), `inputs.py:846-923` (`clear_filter_input_namespace`).

Per the carry-forward from `rev-filters__factories.md` and `rev-filters__base.md`: the filter-subsystem first-cohort GLOSSARY coverage is best authored together at version-bump time per `spec-027` Decision 10's joint-cut deferral pattern, since `RelatedFilter` is the only filter-subsystem symbol with a GLOSSARY entry today (and that one is labeled `shipped (0.0.8)` to match the joint-cut). An in-cycle GLOSSARY edit here for a `0.0.7`-cycle file when the subsystem is labeled `shipped (0.0.8)` would force a status-flip too.

Forwarded to `rev-django_strawberry_framework.md` project pass paired with the `sets_mixins.py` carry-forward (four shared-set symbols absent) and the `rev-filters__factories.md` Low forward (`FilterArgumentsFactory`, `get_filterset_class`, `_dynamic_filterset_cache`, `_make_cache_key` absent) and the `rev-filters__base.md` Low forward (`TypedFilter`, `ArrayFilter`, `ArrayFilterMethod`, `RangeFilter`, `RangeField`, `ListFilter`, `ListFilterMethod`, `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter`, `LazyRelatedClassMixin` absent). No in-cycle GLOSSARY edit.

### Defensive `# pragma: no cover` on `_model_field_for_filter`'s `except Exception` catch-all (`inputs.py:781`) — broad-exception calibration

Site: `inputs.py:778-782`:
```
for part in parts:
    try:
        field = cursor_model._meta.get_field(part)
    except Exception:  # pragma: no cover - defensive: bad lookup path
        return None
```

The `except Exception:` catches every kind of failure from `_meta.get_field(part)`. Django raises `FieldDoesNotExist` for unknown names, but the catch is broad. The defensive nature is correct — a bad lookup path should yield `None` (the "no backing model field" sentinel) rather than crashing the filter-input build. The `# pragma: no cover` is acceptable per `AGENTS.md` rule 12 ("pragma no cover is only for branches genuinely unreachable under the test runner"). This branch IS reachable in principle (declare a `Filter(field_name='nonexistent')`), so the `# pragma: no cover` actually skips reachable behavior.

Why it matters: per `AGENTS.md` rule 12, pragma-no-cover on a reachable branch is a smell. The catch is documented "defensive: bad lookup path" — that path is reachable via any consumer who declares a typo in `field_name`. A test pinning that path would remove the `# pragma` and earn the coverage line through a real consumer-error scenario.

Recommended change: tighten the `except Exception:` to `except FieldDoesNotExist:` (importing `django.core.exceptions.FieldDoesNotExist`) so the catch matches Django's documented contract; pair with a regression test for `_model_field_for_filter` against a `field_name="nonexistent"` filter, and drop the `# pragma: no cover`. The narrower catch surfaces unexpected `_meta.get_field` failures (the real bug class the broad catch masks) instead of silently returning `None`. **Note:** this is a Low because the broad catch is intentional defensive shape per the comment — the recommended tightening is a code-quality improvement, not a bug fix. Worth flagging because the pragma-no-cover on a reachable path is the AGENTS.md rule 12 smell signal.

## What looks solid

### DRY recap

- **Existing patterns reused.** `INPUTS_MODULE_PATH` (`inputs.py:53`) is the single source of truth for the module-path string consumed by `_build_logic_fields` (`inputs.py:611`), the `RelatedFilter` lazy ref in `_build_input_fields` (`inputs.py:696`), and the `sys.modules[INPUTS_MODULE_PATH]` lookup in `materialize_input_class` (`inputs.py:841`) — three sites, one constant, no drift risk. Same shape for `_LOGIC_KEYS` (`inputs.py:114`) — the single source of truth `sets.py::FilterSet._normalize_input` imports and `_build_logic_fields` consumes. The owner-type-name derivation routes through `_owner_type_name` (`inputs.py:545-553`) so the three callers (this helper, `filters/base.py::_expected_global_id_type_name`, `types/finalizer.py::_bind_filterset_owner`) share one derivation rule per the docstring. `_choice_enum_from_filter` (`inputs.py:263-292`) is consumed by both `_element_annotation` (`inputs.py:320`) and `convert_filter_to_input_annotation`'s top-level `ChoiceFilter` branch (`inputs.py:378`) — single error site for the non-`Choices`-derived rejection. The `_iter_filterset_subclasses` helper (`inputs.py:926-950`) is used only by `clear_filter_input_namespace` (`inputs.py:915`) but the dedup-by-identity contract is documented as worth keeping as a private helper.
- **New helpers considered.** Considered hoisting `_unwrap_enum_member` element iteration into a `_unwrap_each(raw_value)` helper consuming three sites (`inputs.py:438`, `inputs.py:444`, `inputs.py:450`) — rejected because the inner call differs per branch (`_encode_global_id_input` vs `_unwrap_enum_member`) and the dispatch IS the branch discrimination. Considered consolidating `BaseCSVFilter` + `(ListFilter, ArrayFilter)` into one `isinstance` tuple — rejected because their per-element logic differs (BaseCSVFilter unwraps enum members AND the element type drives off the model field; ListFilter unwraps enum members only). The list-of-element annotation IS the only true cross-branch duplicate (DRY analysis bullet 3 above).
- **Duplication risk in the current file.** The `[_unwrap_enum_member(item) for item in raw_value]` pattern duplicates between the BaseCSVFilter branch (`inputs.py:444`) and the (ListFilter, ArrayFilter) branch (`inputs.py:450`) — load-bearing because each branch's `isinstance` dispatch is the type signature for the call. Folding both into a single comprehension would lose the documentation value of the per-branch comment. Same for the `getattr(filter_instance, "field", None)` lookup repeated at `inputs.py:323` (in `_element_annotation`) and `inputs.py:383` (in `convert_filter_to_input_annotation`'s catch-all branch) — both are intentional one-line lookups for a defensive optional attribute, not a duplication smell. Intentional sibling design.

### Other positives

- **Branch-order rationale is explicit in `convert_filter_to_input_annotation`'s docstring** (`inputs.py:341-350`): "most-specific to least-specific: the Relay-aware primitives first ... they subclass `Filter` / `MultipleChoiceFilter` and would otherwise fall through to scalar / list" — exactly the kind of rationale-not-restating-code comment that survives refactoring without rot.
- **Defensive UNSET / None guard at the entry to `normalize_input_value`** (`inputs.py:434`) is documented with the *why* (the iteration / scalar branches below would raise `TypeError` or silently pass UNSET) — same shape as the `_choice_enum_from_filter` `model_field is None or not getattr(model_field, "choices", None)` defensive guard (`inputs.py:285`).
- **`build_input_class`'s preference for `type(name, (), namespace)` over `dataclasses.make_dataclass`** (`inputs.py:569-575`) is documented with the *why* (the `strawberry.field` default gets replaced with `dataclasses.Field` and strips the GraphQL alias) — exactly the kind of "this looks suboptimal but here's the load-bearing reason" comment future readers benefit from.
- **`_encode_global_id_input` is documented with the regression it prevents** (`inputs.py:460-475`): the previous implementation eagerly decoded the object down to its bare `node_id` here, stripping the `type_name` BEFORE validation. The wire-form re-encode preserves the type for `GlobalIDFilter.filter`'s validation step. Pinned by `test_normalize_input_value_encodes_globalid_object_to_wire_form` and `test_normalize_input_value_global_id_list`.
- **`HIDE_FLAT_FILTERS` toggle parity with django-graphene-filters is documented in detail at the call site** (`inputs.py:663-675`) including the upstream's throwaway trimmed-subclass + flat-args merge shape and why the strawberry-django shape can collapse the trim into a single skip. Pinned by four `test_build_input_fields_*hide_flat_filters*` tests covering both toggle positions, deep multi-hop, and the non-RelatedFilter flat survival path.
- **`clear_filter_input_namespace`'s "Symmetric with the factory guard above (M-core-4 review)" comment** (`inputs.py:906-909`) explicitly captures the latent-footgun reasoning for using `pass` not `return` in the `except ImportError` block, so a future reader who adds a fourth phase after the FilterSet clear doesn't reintroduce the early-return bug.
- **`_isolate_registry` autouse fixture in `tests/filters/test_inputs.py:58-66`** clears `_field_specs` + `_helper_referenced_filtersets` explicitly — `inputs.py:135-140`'s docstring already documents this contract verbatim ("the filter test files' `_isolate_registry` autouse fixture clears this map explicitly for exactly that reason"). Test-code-and-source-comment-as-audit-trail symmetry maintained.
- **Materialized class objects are intentionally left parked in `filters.inputs.__dict__` per `clear_filter_input_namespace`'s docstring** (`inputs.py:863-876`) — the reasoning (consumer LazyType resolution would `AttributeError` if the matching module global had been `delattr`'d) is captured verbatim, including the specific consumer fixture (`test_scalars_api.py`'s per-app reload). The reset-the-ledger-but-leave-the-module-global pattern is a load-bearing decision documented well enough that a future "let's clean up the ledger" patch won't break consumer-side LazyType references.
- **`_pascal_case`'s `ConfigurationError` raises at the call site for empty / no-word inputs** (`inputs.py:174-179`) so the failure surfaces the real cause rather than a downstream collision against a generic `"FilterInputType"`. Pinned by `test_pascal_case_raises_for_no_word_character_input` for `""` / `"_"` / `"__"` / `"___"`.

### Summary

A 951-line filter-input scaffolding + converter module (Slice 1 + Slice 2 + Slice 3 lineage all shipped) with five control-flow hotspots (`_scalar_from_form_field` 44 lines / 10 branches, `convert_filter_to_input_annotation` 65 lines / 12 branches, `normalize_input_value` 49 lines / 8 branches, `_build_input_fields` 132 lines / 15 branches, `clear_filter_input_namespace` 78 lines / 7 branches) but every hotspot is dispatch-shaped, well-documented, and pinned by direct unit tests in `tests/filters/test_inputs.py`. Zero High. Two real Mediums: (a) `_build_input_fields` produces a colliding bag-class name when `top_name` has no word characters because `type_name_for` routes through `utils.strings.pascal_case` (not `inputs._pascal_case`) and bypasses the no-word-character guard — the canonical fix is hoisting the guard to `sets_mixins.py::type_name_for`; (b) `_normalize_range_value` always returns both positional axes with `None`-valued keys for missing axes, which works for `django-filter` today but cements a divergent contract — the fix is dropping `None`-valued axes from the returned patch. Six Lows: spec-021 → spec-027 citation drift (forwarded to folder pass; no in-cycle edit), Slice 1 / 2 / 3 tense-rot in docstrings (comment-pass), `_pascal_case` error-message direct-vs-indirect caller calibration (comment-pass), `_unwrap_enum_member` one-level unwrap depth undocumented (comment-pass), GLOSSARY coverage gap for 13 backticked symbols (forwarded to project pass), and broad-`except Exception` + pragma-no-cover on a reachable `_model_field_for_filter` path (`AGENTS.md` rule 12 calibration; tighten to `FieldDoesNotExist` + earn the coverage line). Standard three-spawn cycle — both Mediums require real source edits AND regression tests; shape-#5 does not qualify.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/sets_mixins.py` — added `from .exceptions import ConfigurationError` and hoisted the no-word-character guard into `ClassBasedTypeNameMixin.type_name_for`. When `field_path` is supplied but every `LOOKUP_SEP`-split segment pascal-cases to the empty string (`""`, `"_"`, `"__"`, `"___"`), the classmethod now raises `ConfigurationError` naming both `cls.__name__` and the offending `field_path` repr. The previous body silently collapsed to `f"{cls.__name__}InputType"`, colliding with the root type's own name. Option (a) of the artifact's recommended fix — the canonical "fixes the guard once and protects all callers" path; `_pascal_case` in `inputs.py` keeps its own guard for the `_build_range_input_class` direct consumer.
- `django_strawberry_framework/filters/inputs.py` — `_normalize_range_value` now drops `None`-valued axes from the returned patch. The both-axes-supplied path is unchanged; partial-range inputs surface only the supplied positional key (`{<base>_0}` for start-only, `{<base>_1}` for end-only, `{}` for neither). Comment block above the new branch explains the divergence-prevention rationale and mirrors `normalize_input_value`'s `is None or is UNSET` rigor.
- `django_strawberry_framework/filters/inputs.py` — tightened `_model_field_for_filter`'s `except Exception:  # pragma: no cover` to `except FieldDoesNotExist:` with a local import (matches the pattern at `types/definition.py:139`). The `# pragma: no cover` is dropped since the path is now exercised by the new typo-field-name regression test (the artifact's Low #6 calibration: the branch was reachable; the pragma masked the AGENTS.md rule 12 smell).

### Tests added or updated

- `tests/filters/test_inputs.py::test_type_name_for_raises_for_no_word_character_field_path` — parametrized over `""` / `"_"` / `"__"` / `"___"`; constructs a bare `ClassBasedTypeNameMixin` subclass and asserts `ConfigurationError` whose message contains the `field_path` repr. Pins Medium #1.
- `tests/filters/test_inputs.py::test_normalize_input_value_range_filter_drops_none_axes_partial_range` — pins all four partial-range shapes (only-start, only-end, both, neither). Pins Medium #2; the existing `test_normalize_input_value_range_filter_emits_positional_keys` continues to pin the both-axes path verbatim.
- `tests/filters/test_inputs.py::test_model_field_for_filter_returns_none_for_unknown_field_name` — pins Low #6's typo-field-name path; earns the coverage line the dropped `# pragma: no cover` previously masked.

### Validation run

- `uv run ruff format django_strawberry_framework/sets_mixins.py django_strawberry_framework/filters/inputs.py tests/filters/test_inputs.py` — pass, no changes (3 files left unchanged).
- `uv run ruff check --fix django_strawberry_framework/sets_mixins.py django_strawberry_framework/filters/inputs.py tests/filters/test_inputs.py` — pass, no fixes needed (all checks passed).
- Repo-wide `uv run ruff format .` / `uv run ruff check --fix .` BOTH fail with a parse error at `django_strawberry_framework/types/base.py:247` — a pre-existing dirty path at task start (`git status --short` lists `types/base.py` as `M` before any of this cycle's edits), out of scope per AGENTS.md rule 33. My touched files all pass cleanly; the repo-wide failure is not attributable to this cycle.

### Notes for Worker 3

- **Pre-existing dirty `types/base.py` syntax error** blocks `uv run ruff format .` / `uv run ruff check --fix .` at the repo level. Confirmed dirty at task start per `git status --short` (one of 12 modified `django_strawberry_framework/*.py` files and several test files). Per AGENTS.md rule 33 ("unexpected file modifications [...] are presumptively the maintainer's or another dev's in-progress work [...] ignore them as out-of-scope"), I left it alone. File-scoped ruff on my three touched files passes both commands cleanly.
- **Medium #1 placement choice.** Worker 1's artifact offered options (a) "hoist to `sets_mixins.py::type_name_for`" and (b) "defensive `_pascal_case` call in `_build_input_fields`". I took (a) per the artifact's own "higher-quality fix" framing and `AGENTS.md` rule 4 ("when multiple fixes exist always recommend the highest-quality one even when it costs more engineering time"). The guard now protects every future caller (`OrderSet` / `AggregateSet` per the mixin's docstring) instead of just the one inputs.py call site.
- **`_pascal_case`'s own guard kept in place.** `_build_range_input_class` calls `_pascal_case(field_name)` directly (not through `type_name_for`); the local guard remains the surfacing site for a `RangeFilter` declared with a `field_name=""` / `field_name="__"`. Two guards covering two distinct paths — not redundant duplication. (Low #3's docstring rewrite about direct-vs-indirect callers is comment-pass material and will be visited then.)
- **Medium #1 regression test shape.** The artifact suggested "declare a `FilterSet` with a filter attribute named `\"__\"`"; I instead pin the guard directly through a bare `ClassBasedTypeNameMixin` subclass because (i) Python class-body assignment of `__ = X` runs into `django_filters.FilterSetMetaclass`'s declared-filter discovery, whose interaction with literally-`__`-named attributes is itself fragile (the attribute may not even reach `_build_input_fields`); (ii) the guard's job is to protect every `type_name_for` caller, including future `OrderSet` / `AggregateSet`, so pinning at the mixin level is the cleaner contract. The integration path is exercised by the existing `_build_input_fields` test surface — any future caller passing `python_attr="__"` (or `""` / `"_"`) trips this guard.
- **Low #6 placement choice.** Kept the `except FieldDoesNotExist` branch reachable through a real test fixture (`tests.filters.fixtures.filtersets.ShelfFilter`, already used by the sibling `test_model_field_for_filter_returns_none_without_field_name`). The narrower catch matches Django's documented contract per `types/definition.py:139`; an unexpected `_meta.get_field` failure (e.g. a future Django version's signal change) now surfaces loudly rather than silently degrading to `None`.
- **No shadow file used.** Implementation followed source directly.

---

## Verification (Worker 3)

### Logic verification outcome

- **Medium #1 (`type_name_for` no-word-character guard).** Confirmed hoisted to `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` lines 61-84: the classmethod now joins `pascal_case(part)` segments and raises `ConfigurationError` when the joined result is empty, with the message citing both `cls.__name__` and `repr(field_path)`. The new docstring at lines 65-72 explicitly names the protected callers (`_build_input_fields` operator-bag naming + future `OrderSet` / `AggregateSet` per-field naming). This is the artifact's recommended option (a) — the canonical "fix the guard once and protect all callers" path. `_pascal_case`'s own guard in `inputs.py` remains in place for the direct `_build_range_input_class` consumer per Worker 2's note (two guards covering two distinct call paths, not redundant).
- **Medium #2 (`_normalize_range_value` drops None axes).** Confirmed at `django_strawberry_framework/filters/inputs.py:542-554`: the function now builds a `patch: dict[str, Any] = {}` and conditionally inserts `{base}_0` / `{base}_1` only when `start is not None` / `end is not None`. The comment block at 542-548 mirrors `normalize_input_value`'s `is None or is UNSET` rigor exactly as the artifact recommended. Both-axes path unchanged; partial-range / neither-axis paths now match the form-data convention.
- **Low #6 (`_model_field_for_filter` narrowed catch).** Confirmed at `django_strawberry_framework/filters/inputs.py:777` (local `from django.core.exceptions import FieldDoesNotExist`) and `inputs.py:795` (`except FieldDoesNotExist:` replacing the prior broad `except Exception:  # pragma: no cover`). Comment block at 796-800 documents the contract (Django's documented exception class for unknown names; anything else surfaces loudly). The `# pragma: no cover` is dropped; the path is now earned by the new regression test.
- **Regression tests verified present and passing.** All three claimed test names grep-confirmed at the expected lines:
  - `test_type_name_for_raises_for_no_word_character_field_path` at `tests/filters/test_inputs.py:679` — parametrized over `""`, `"_"`, `"__"`, `"___"`; instantiates a bare `_Probe(ClassBasedTypeNameMixin)` subclass and asserts `ConfigurationError` with `repr(bad)` in the message. Pins Medium #1.
  - `test_normalize_input_value_range_filter_drops_none_axes_partial_range` at `tests/filters/test_inputs.py:450` — pins all four partial-range shapes (only-start, only-end, both, neither). Pins Medium #2.
  - `test_model_field_for_filter_returns_none_for_unknown_field_name` at `tests/filters/test_inputs.py:840` — pins typo-field-name through the real `ShelfFilter` fixture. Earns the coverage line the prior `# pragma: no cover` masked.
- **Focused pytest result.** `uv run pytest tests/filters/test_inputs.py -x -k "type_name_for or range_filter or model_field_for_filter"` — 10 passed, 0 failed (coverage gate FAIL is expected under focused-`-k`, not attributable to this cycle). Full-file run `uv run pytest tests/filters/test_inputs.py` — 62 passed, 0 failed (no sibling regressions).
- **Medium #1 placement rationale accepted.** Worker 2 chose option (a) over (b) per `AGENTS.md` rule 4 ("recommend the highest-quality fix even when it costs more engineering time"); hoisting the guard into the shared mixin protects every future `OrderSet` / `AggregateSet` per-field caller, not just the one inputs.py call site. The regression test pins at the mixin level (bare `ClassBasedTypeNameMixin` subclass) rather than through a contrived `FilterSet` declaration named `"__"`, which is the cleaner contract per the docstring's scope. Accepted as recorded.
- **Pre-existing dirty `types/base.py` parse error.** Worker 2's Notes-for-Worker-3 flagged a pre-existing `types/base.py:247` syntax error blocking repo-wide `ruff`. Spot-confirmed `git status --short` shows no `types/base.py` modification at verification time (it was scoped to `docs/review/review-0_0_7.md`); the maintainer's `5b2788f` cohort included the file in the consolidated framework polish so the dirty path Worker 2 saw is now committed clean. File-scoped ruff on `sets_mixins.py` + `inputs.py` + `test_inputs.py` passes per Worker 2's report — no in-cycle ruff issue.

### DRY findings disposition

All four `Defer-with-trigger` DRY bullets carry forward unchanged — Worker 2 did not introduce a refactor that would advance the trigger condition for any of them. The `_normalize_range_value` dict/object accessor pair (DRY bullet 1) was edited in this cycle to add the None-axis drop logic but the dual `isinstance(raw_value, dict)` discriminator pattern at lines 534-541 is unchanged; the helper-promotion trigger ("third positional-key Range axis OR second filter primitive with the same dataclass-or-dict pattern") still gates the consolidation.

### Temp test verification

No temp test files needed. The three permanent regression tests in `tests/filters/test_inputs.py` (cited above) are sufficient proof that each fix exercises its intended branch; verifying-by-rerun under the runner is the canonical check.

### Verification outcome

`logic accepted; awaiting comment pass` — top-level `Status:` flipped to `logic-accepted`. Both Mediums and Low #6 land cleanly with regression tests; no false-premise rejections to spot-check; no sibling regressions in `tests/filters/test_inputs.py`. Comment pass should visit Lows #1 (forwarded — no-op), #2 (Slice tense-rot), #3 (`_pascal_case` error-message direct-vs-indirect calibration), #4 (`_unwrap_enum_member` one-level unwrap depth doc), and #5 (GLOSSARY forward — no-op).

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/filters/inputs.py:2-16` — module docstring: dropped Slice 1 / 2 / 3 in-flight framing in favor of the present module composition (constants + converter pair + dataclass builder + per-filterset operator-bag helpers + module-global materialization / namespace-clear pair). All those subsystems shipped at 0.0.7; the prior "Slice 1 landed ..., Slice 2 adds ..., Slice 3 lands ..." sequencing read as audit-trail rather than module description and rotted out of tense.
- `django_strawberry_framework/filters/inputs.py:66-73` — `LOOKUP_NAME_MAP` comment: dropped "Slice 1 consumes ... / Slice 2 consumes ..." per-slice attribution, replaced with concrete consumer-site references (`FilterSet._normalize_input`, `_build_input_fields`, `normalize_input_value`). Same rewording per the artifact's Low #2 recommendation.
- `django_strawberry_framework/filters/inputs.py:121-126` — `FieldSpec` docstring: stripped "(Slice 3's)" qualifier from the `materialize_input_class` reference. The helper has shipped; the parenthetical no longer disambiguates.
- `django_strawberry_framework/filters/inputs.py:144-150` — `_materialized_names` comment: dropped "Slice 3's" prefix on the `materialize_input_class` write contract; rest of the cleanup-contract description unchanged.
- `django_strawberry_framework/filters/inputs.py:811-816` — `construct_search` docstring: softened "Spec sub-bullet 4 for Slice 2 lands the helper now" to "Landed now even though the `Meta.search_fields` card is deferred to `0.1.2`" since Slice 2 no longer disambiguates against any future slice; the deferred-companion-card framing carries forward.
- `django_strawberry_framework/filters/inputs.py:428` — `normalize_input_value` docstring: "Per the Implementation discretion item (Slice 2 plan step 2)" rewritten to "Per the spec-021 Implementation-discretion item" (Slice 2 plan step 2 no longer disambiguates against any future plan).
- `django_strawberry_framework/filters/inputs.py:162-180` — `_pascal_case` docstring + error message tightened per Low #3 direct-vs-indirect caller precision. Added a paragraph naming the one direct consumer today (`_build_range_input_class`) and the indirect callers that route through `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` and trip its sibling no-word-character guard (the Medium #1 hoist from the logic pass). Error-message wording narrowed from "rename the filter / field" to "rename the RangeFilter's `field_name=`" so the error surfaces the specific surfacing path. The existing pinning test `test_pascal_case_raises_for_no_word_character_input` asserts only `repr(bad) in str(excinfo.value)` (not the prose) and continues to pass.
- `django_strawberry_framework/filters/inputs.py:482-501` — `_unwrap_enum_member` docstring extended with the Low #4 one-level-unwrap depth note: the helper does NOT recurse into nested-list / nested-dict shapes; no current Django-converter-pipeline consumer produces such inputs, but a future nested-shape `ListFilter` would need its own per-level walk.
- `django_strawberry_framework/filters/inputs.py:524-543` — `_normalize_range_value` docstring extended to describe the Medium #2 partial-range emission contract: returns `{<name>_0}` for start-only inputs, `{<name>_1}` for end-only, `{}` for neither. The both-axes return shape is unchanged; the doc-string now describes the four shapes the function can legitimately return so any caller walking `patch.keys()` sees the "axis supplied" semantics the Medium #2 fix preserves.

### Per-finding dispositions

- Medium 1 (`type_name_for` no-word-character guard hoisted to `sets_mixins.py`): logic-pass change carried no docstring drift; the existing `_input_type_name_for` docstring already says the spec-021 naming rule lives on the mixin. No additional comment-pass edit beyond Low #3 below.
- Medium 2 (`_normalize_range_value` drops `None`-valued axes): docstring extended at `inputs.py:524-543` to describe the four return shapes (`{}` / `{<name>_0}` / `{<name>_1}` / both). The new comment block at lines 542-548 (added in the logic pass) already documents the in-source rationale; this is the docstring-side complement.
- Low 1 (spec-021 → spec-027 citation drift): forwarded to folder pass per the dispatch — NO in-cycle edit here. 13 sites unchanged in this file.
- Low 2 (Slice 1 / 2 / 3 tense-rot): five sites touched per the Files-touched list above. The `_pascal_case` docstring's pre-existing `(round-4 fix)` framing was left intact (test-tag pin, not a Slice label).
- Low 3 (`_pascal_case` direct-vs-indirect caller precision): docstring paragraph added at `inputs.py:170-176`; error message tightened to name the RangeFilter `field_name=` consumer. Both deltas in one edit; existing test continues to pass.
- Low 4 (`_unwrap_enum_member` one-level unwrap depth): docstring paragraph added at `inputs.py:497-501`. No code change.
- Low 5 (GLOSSARY coverage gap): forwarded to project pass per the dispatch — NO in-cycle edit here.
- Low 6 (`_model_field_for_filter` broad-`except` + pragma-no-cover): logic-pass change already shipped narrowed `FieldDoesNotExist` catch + dropped pragma with the new comment block at `inputs.py:796-800`; the prior docstring at line 776 ("Resolve the Django model field a filter targets (or `None`).") still accurately describes the contract — `None` for unknown / missing field, raise for any other failure. No further comment-pass edit needed.

### Validation run

- `uv run ruff format django_strawberry_framework/filters/inputs.py` — pass, no changes.
- `uv run ruff check --fix django_strawberry_framework/filters/inputs.py` — pass, no fixes.
- Repo-wide `uv run ruff format .` — pass, 198 files left unchanged (the `types/base.py` parse error Worker 2 saw at logic-pass dispatch was committed clean in the maintainer's `5b2788f` cohort per Worker 3's verification note; the repo-wide format now succeeds).
- Repo-wide `uv run ruff check --fix .` — pass, all checks passed.
- `uv.lock` unchanged.

### Notes for Worker 3

- **Existing `_pascal_case` test pin survives the error-message rewording.** `tests/filters/test_inputs.py:658-662` asserts only `repr(bad) in str(excinfo.value)` (not the prose), and the new wording still embeds the `repr(bad)` token through the f-string. No test edit required.
- **Slice tense-rot sweep scope.** Seven sites touched (module docstring, LOOKUP_NAME_MAP comment, FieldSpec docstring, _materialized_names comment, `normalize_input_value` docstring, `construct_search` docstring, plus the one-line removal of "(Slice 3's)" from `FieldSpec`). All Slice tokens removed from prose; the pinning test commentary `(round-4 fix)` left in place per its review-tag function. `grep "Slice " django_strawberry_framework/filters/inputs.py` returns zero hits after this pass.
- **Forwarded Lows untouched.** Low 1 (spec-021 → spec-027 drift, 13 sites in this file) and Low 5 (GLOSSARY coverage gap for 13 backticked symbols) are both forwarded to higher-scope passes per the dispatch — staying out of scope per the worker-2.md "no unrelated cleanup" rule.

---

## Changelog disposition

### State

`Warranted but deferred to maintainer`.

### Reason

Two consumer-visible behavior changes landed this cycle, both arriving on the same `filters/` subsystem cohort that the maintainer is staging for the `0.0.8` joint-cut (per `spec-027` Decision 10's joint-cut deferral pattern already applied to `filters/base.py::RelatedFilter` earlier this release):

- **Medium #1 — `ClassBasedTypeNameMixin.type_name_for` typed-error contract change.** The mixin lives in `django_strawberry_framework/sets_mixins.py` and its `type_name_for` classmethod is the shared public derivation point that consumers of `FilterSet` (and the forthcoming `OrderSet` / `AggregateSet` per the mixin's docstring) inherit. Hoisting the no-word-character guard from `_pascal_case` (a private helper in `filters/inputs.py`) into the shared mixin promotes the `ConfigurationError` from an inputs.py-local raise into a typed-error contract on every future consumer of the mixin. This is a public-API typed-error contract change. The existing `[Unreleased] ### Changed` bullet for `_pascal_case` (CHANGELOG.md:26) covers only the inputs.py-local guard; the new `type_name_for` guard is a distinct, broader surface and warrants its own entry. **Mirrors the `filters/base.py::RelatedFilter` `TypeError` precedent** from earlier this cycle (recorded in `worker-memory/worker-2.md` under `## filters/base.py`).
- **Medium #2 — `_normalize_range_value` partial-range axis-drop.** The helper itself is private (leading underscore in `filters/inputs.py`) but its return shape is the form-data patch that `FilterSet._normalize_input` merges into the `django-filter` form-data dict. The behavior change is observable through `RangeFilter`'s partial-input handling: where a `start=5, end=None` input previously surfaced both `{base}_0` and `{base}_1` keys (the second with `None`), it now surfaces only `{base}_0`. This is a strict bug-fix that aligns implementation with the docstring's "positional form-data patch" framing (the patch now matches what `django-filter` actually expects for partial ranges per `RangeWidget.value_from_datadict`'s "field not supplied" convention). Worth recording so any consumer who happened to introspect the patch's keys (logging, audit, debug) sees the contract pinned.

Low #6 (`FieldDoesNotExist` tightening on `_model_field_for_filter`) is an internal-only error-type narrowing in a private helper that no consumer reaches; not warranted on its own.

The active plan (`docs/review/review-0_0_7.md`) does NOT authorize a `CHANGELOG.md` edit for this cycle. Per `AGENTS.md` rule 21 ("Do not update `CHANGELOG.md` unless explicitly instructed") and the pre-alpha maintainer-owned CHANGELOG cadence, the entries below are preserved verbatim under `### Suggested CHANGELOG entry` so the maintainer can lift them into `[Unreleased]` at the `0.0.8` cut without re-derivation.

### What was done

No `CHANGELOG.md` edit. The suggested entry text below is preserved verbatim for the maintainer.

### Suggested CHANGELOG entry

To be added under `[Unreleased] ### Changed` (the same joint-cut cohort as the existing `RelatedFilter` `TypeError` and `_pascal_case` `ConfigurationError` bullets, all part of the `0.0.8` filtering-subsystem ship):

```
- `ClassBasedTypeNameMixin.type_name_for` (the shared mixin classmethod inherited by [`FilterSet`][glossary-filterset] and the forthcoming `OrderSet` / `AggregateSet`) now raises [`ConfigurationError`][glossary-configurationerror] when every `LOOKUP_SEP`-split segment of `field_path` pascal-cases to the empty string (e.g. `field_path="_"`, `"__"`, `"___"`). The pre-fix code silently produced `f"{cls.__name__}InputType"`, colliding with the root input type's own name. The error message names both `cls.__name__` and the offending `repr(field_path)` so the consumer sees an actionable site. Companion to the `_pascal_case` `ConfigurationError` already recorded above — the inputs.py-local helper guards the `_build_range_input_class` direct-consumer path; this mixin-level guard protects every future caller of `type_name_for`. Only relevant for synthetic test fixtures or single-underscore module-private classes — no real-world consumer FilterSet, OrderSet, or AggregateSet name should be affected.
- `RangeFilter` partial-range inputs now produce a positional form-data patch that contains only the supplied axes. Previously `_normalize_range_value` (the private helper consumed by `FilterSet._normalize_input` for `django-filter`'s `RangeWidget.value_from_datadict` contract) always returned both `{base}_0` and `{base}_1` keys with `None` for missing axes; it now returns `{base}_0` for start-only, `{base}_1` for end-only, both for fully-supplied, and `{}` for neither. The behavior change aligns the helper's return shape with the docstring's "positional form-data patch" framing — `django-filter` already short-circuited on the `None`-valued keys at the form-data layer, so the consumer-visible filter behavior is unchanged; the observable difference is in any caller that inspects `patch.keys()` (logging, audit, debug) which now sees true "axis supplied" semantics instead of the prior "always both, possibly with `None`".
```

### Validation run

- `uv run ruff format .` — pass, 198 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed.

---

## Iteration log

## Verification (Worker 3, pass 2 — comment-verify)

### Comment verification outcome

- **Slice tense-rot scrub (Low #2).** `grep -c "Slice " django_strawberry_framework/filters/inputs.py` returns `0`. All seven sites Worker 2's report enumerated (module docstring at 2-16, `LOOKUP_NAME_MAP` comment at 66-73, `FieldSpec` docstring at 121-126, `_materialized_names` comment at 144-150, `normalize_input_value` docstring at 428, `_pascal_case` docstring untouched re: Slice — only the `(round-4 fix)` review tag left intact per the note, and the `construct_search` docstring at 811-816) verified in the unstaged diff. The `(round-4 fix)` survival is correct — it is a review-tag pin, not a Slice label, and would not grep-match the audit. The module docstring rewrite reads as composition-narrative (constants + converter pair + dataclass builder + per-filterset helpers + module-global pair) rather than Slice sequencing — exactly the tense-correct framing the artifact recommended.
- **`_pascal_case` error message + direct-vs-indirect caller note (Low #3).** Confirmed at `django_strawberry_framework/filters/inputs.py:162-184`. The docstring now opens with the empty-token rationale, then closes with a dedicated "Direct caller today: `_build_range_input_class` only. Indirect callers ... route through `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` and trip its sibling no-word-character guard rather than this one" paragraph. The error string narrowed from `"rename the filter / field"` to `"rename the RangeFilter's \`field_name=\`"` — names the immediate surfacing consumer. The pre-existing test `test_pascal_case_raises_for_no_word_character_input` at `tests/filters/test_inputs.py:658-662` asserts only `repr(bad) in str(excinfo.value)`, so the rewording does not break the pin (the `f"_pascal_case received {name!r}..."` still embeds `repr(bad)`).
- **`_unwrap_enum_member` one-level depth note (Low #4).** Confirmed at `django_strawberry_framework/filters/inputs.py:497-502`. The docstring extension reads "Single-level unwrap — nested-list / nested-dict inputs are not recursively unwrapped. No current consumer produces such shapes (the Django converter pipeline yields flat scalars / lists from the django-filter form-field hierarchy); a future nested-shape `ListFilter` would need its own per-level walk." Matches the artifact's recommended phrasing exactly — flags the depth limit and names the future-spec scenario where a per-level walk would become necessary.
- **`_normalize_range_value` four return shapes documented (Medium #2 doc complement).** Confirmed at `django_strawberry_framework/filters/inputs.py:535-548`. The pre-existing prose at 535-542 describes the both-axes `{<name>_0, <name>_1}` return shape and the form-data field-name derivation. The new paragraph at 544-548 enumerates the three remaining shapes (`{<name>_0}` start-only, `{<name>_1}` end-only, `{}` neither) and explains the "axis not supplied" form-data convention preservation. All four legitimate return shapes from the function are now docstring-described — any caller walking `data.keys()` sees the documented contract.
- **Forwarded Lows untouched (Lows #1 + #5).** Confirmed by diff inspection: zero `spec-021` → `spec-027` rewrites in the unstaged diff for `inputs.py`, zero GLOSSARY additions for the 13 backticked symbols. Worker 2's Notes-for-Worker-3 explicitly recorded the deferral; the folder-pass and project-pass artifacts are the right scope per the dispatch.

### DRY findings disposition

No DRY changes in this pass (comment-pass scope). The four `Defer-with-trigger` bullets remain unchanged — no helper-promotion trigger advanced.

### Temp test verification

None needed. Existing `test_pascal_case_raises_for_no_word_character_input` continues to pin the `_pascal_case` error path through the rewording (the `repr(bad)` token survives the narrower message); the three logic-pass regression tests (cited in `## Verification (Worker 3)` pass 1 above) cover all three real-source edits from the prior pass.

### Validation run

- `git diff django_strawberry_framework/filters/inputs.py | wc -l` = `150` lines — diff scope confined to seven docstring sites + one `LOOKUP_NAME_MAP` comment + one `_materialized_names` comment + the `_pascal_case` error-string narrowing. No logic changes.
- `grep -c "Slice " django_strawberry_framework/filters/inputs.py` = `0`. Tense-rot fully scrubbed.
- `git diff -- CHANGELOG.md` empty (expected for "awaiting changelog disposition" status).
- Repo-wide ruff (per Worker 2's report): `uv run ruff format .` passes (198 files left unchanged); `uv run ruff check --fix .` passes (all checks). The pre-existing `types/base.py` parse error Worker 2 saw at logic-pass dispatch was committed clean in the maintainer's `5b2788f` cohort per pass-1 verification.

### Verification outcome

`comments accepted; awaiting changelog disposition` — top-level `Status:` flipped to `comments-accepted`. All five comment-pass deliverables landed cleanly (Slice tense scrub, `_pascal_case` calibration, `_unwrap_enum_member` depth doc, `_normalize_range_value` four-shape doc, forwarded Lows untouched). Worker 2 should now author the changelog disposition (one of three states) and dispatch the terminal-verify pass.

## Verification (Worker 3, pass 3 — terminal-verify)

### Terminal verification outcome

- **Changelog diff empty.** `git diff -- CHANGELOG.md` returns no output — matches the "Warranted but deferred to maintainer" disposition.
- **Verbatim maintainer-ready entry present.** Fenced `### Suggested CHANGELOG entry` block at artifact lines 284-287 contains two bullets covering (1) the `ClassBasedTypeNameMixin.type_name_for` typed-error contract change with both `cls.__name__` and `field_path` surfacing, and (2) the `RangeFilter` partial-range axis-drop with the four observable return shapes. Both bullets are lift-ready under `[Unreleased] ### Changed` at the `0.0.8` joint-cut, naming the existing `RelatedFilter` `TypeError` + `_pascal_case` `ConfigurationError` cohort siblings for placement.
- **"Real consumer-visible change" framing honest.** `ClassBasedTypeNameMixin` is exported via `django_strawberry_framework/sets_mixins.py::__all__` line 127 and inherited by the public `FilterSet` at `django_strawberry_framework/filters/sets.py:172` (`class FilterSet(ClassBasedTypeNameMixin, filterset.BaseFilterSet, metaclass=FilterSetMetaclass)`). The forthcoming `OrderSet` is already wired to the same mixin per `orders/inputs.py:15-16` comments. The hoisted `ConfigurationError` on `type_name_for` is therefore a genuine public-API typed-error contract change on an inheritance surface every set subclass shares — not internal-only. The deferral state matches the precedent set by `filters/base.py::RelatedFilter`'s `TypeError` contract change earlier this release.
- **Logic + comment passes already accepted.** Passes 1 (logic) and 2 (comment) acceptances stand; spot-confirmed source state at verification time: `sets_mixins.py:78-83` (`ConfigurationError` raise), `filters/inputs.py:566-571` (`patch: dict[str, Any]` build with `is not None` guards), `filters/inputs.py:777` (`from django.core.exceptions import FieldDoesNotExist`) + `:795` (`except FieldDoesNotExist:` no pragma). `grep "Slice " django_strawberry_framework/filters/inputs.py` returns 0 hits — tense-rot scrub holds.
- **Ruff outcomes recorded.** Comment-pass validation block (artifact lines 245-249) recorded `uv run ruff format .` pass (198 files unchanged) and `uv run ruff check --fix .` pass (all checks). The prior `types/base.py:247` parse error Worker 2 flagged at logic-pass dispatch was landed clean in maintainer's `5b2788f` cohort per pass-1 verification.

### Validation run

- `git diff -- CHANGELOG.md` empty (terminal-verify required).
- `git status` confirms only `filters/inputs.py`, `docs/review/rev-filters__inputs.md`, and `docs/review/review-0_0_7.md` modified (the rev artifact + the checklist mark this pass writes; the inputs.py edits from the prior passes).

### Verification outcome

`cycle accepted; verified` — top-level `Status:` flipped to `verified`. Marking the `django_strawberry_framework/filters/inputs.py` checkbox in `docs/review/review-0_0_7.md` and appending the memory entry.
