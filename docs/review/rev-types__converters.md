# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## DRY analysis

- Defer until a third postgres-contrib field is soft-registered (candidates: `CIText`, range fields); collapse `_resolve_array_field` (`converters.py:89-99`) and `_resolve_hstore_field` (`converters.py:102-112`) into a single `_resolve_postgres_field(attr_name: str) -> type[models.Field] | None` helper. Today both six-line bodies are verbatim except for the attribute symbol; the docstring is also a verbatim mirror with one word swapped. The trigger is "third soft-imported postgres field" — at that point the helper saves real bytes and the module-level `_X_FIELD_CLS = _resolve_postgres_field("X")` pattern becomes idiomatic. Two sites is below the threshold for an extraction; the shared shape is short, the differing token is load-bearing for `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", ...)` test ergonomics, and a helper would slightly obscure which postgres field each module-level constant binds to.
- Defer until the `convert_scalar` ArrayField / HStoreField branches gain a third sentinel-guarded postgres-field branch (next candidate: `CIText` family routing to `str`); extract `_postgres_branch(field, sentinel, *, on_choices_message: str, build: Callable[[models.Field], Any]) -> Any | None` helper from `converters.py:194-207` and `converters.py:212-221`. Both branches share the same five-step shape (sentinel-None short-circuit / `isinstance` test / outer-`choices` rejection with field-shape-specific message / per-branch synthesis / outer-`null` widening). The differing surface is the choices-rejection message body and the synthesis step (`list[inner]` vs `strawberry.scalars.JSON`), so the helper signature has to accept both as parameters — at two sites the helper adds parameter-count weight without clear payoff. Trigger fires when the third branch lands and the synthesis-step diversity is what justifies the abstraction.
- Defer until a fourth `_sanitize_member_name` rewrite rule lands (current rules: ASCII-non-ident → leading-digit → keyword → GraphQL-reserved/dunder); convert the three-step rewrite chain at `converters.py:247-253` to a table-driven `_MEMBER_NAME_RULES: tuple[tuple[Callable[[str], bool], Callable[[str], str]], ...]` loop. Today three rules read cleaner inline than as a tuple; a fourth rule with conditional-prefix logic would tip the balance.

## High:

None.

## Medium:

None.

## Low:

### `convert_choices_to_enum` `Raises:` docstring omits the sanitized-member-collision raise

`converters.py::convert_choices_to_enum`'s `Raises:` block at `converters.py:274-276` documents only the grouped-choices and empty-choices `ConfigurationError` paths, but the function body raises a third documented-by-tests `ConfigurationError` at `converters.py:319-322` when two choice values sanitize to the same Python identifier (e.g. `("a-b", ...)` and `("a_b", ...)` both → `"a_b"`; or `("if", ...)` and `("_if", ...)` both → `"_if"`; or `("true", ...)` and `("MEMBER_true", ...)` both → `"MEMBER_true"`). Three regression tests pin this contract — `tests/types/test_converters.py::test_convert_choices_to_enum_raises_on_sanitized_member_collision` (293), `::test_convert_choices_to_enum_raises_on_keyword_prefix_collision` (314), `::test_convert_choices_to_enum_raises_on_graphql_safe_name_collision` (334) — and the test rationale explicitly cites "Pins the Medium fix from rev-types__converters.md" so the contract is a published shape, not an internal accident. The docstring under-promises: a future consumer reading the function's contract would not see "sanitize to the same enum member" as a catchable shape.

Recommended fix: extend the `Raises:` block to a third sub-bullet (mirroring the `convert_scalar` `Raises:` enumeration style):

```docstring
Raises:
    ConfigurationError: triggered by any of the following:

        - ``field.choices`` is empty — declared but the sequence is empty.
        - ``field.choices`` contains nested tuples (Django's grouped-choices
          form). Only the flat ``(value, label)`` form is supported.
        - two or more choice values sanitize to the same enum member
          (e.g. ``"a-b"`` and ``"a_b"`` both collapse to ``"a_b"``);
          rename one side or split into separate fields.
```

```django_strawberry_framework/types/converters.py:274:284
    Raises:
        ConfigurationError: ``field.choices`` contains nested tuples
            (Django's grouped-choices form) or is empty.
    """
    choices = list(field.choices or [])
    if not choices:
        raise ConfigurationError(
            f"{field.model.__name__}.{field.name} declares choices but the "
            "sequence is empty; choices must be a non-empty flat sequence "
            "of (value, label) pairs.",
        )
```

### `convert_choices_to_enum` numbered-step docstring lists 7 steps but step 1 ("Reject grouped-choices form") elides the empty-choices reject and the collision reject

The docstring at `converters.py:258-277` enumerates a seven-step algorithm but step 1 ("Reject Django's grouped-choices form") implicitly bundles the empty-choices guard (raised before the grouped loop at `converters.py:279-284`) AND step 5 ("Build the Enum") implicitly bundles the collision-rejection raise at `converters.py:314-322`. A reader following the seven steps top-to-bottom would not match them to source line numbers without inferring two more raise paths. Same citation-hygiene Low calibration as `rev-types__base.py`'s discoverability Lows — the function's actual contract surface is wider than the docstring promises.

Recommended fix: rewrite the numbered list as a faithful map of the function body, ideally interleaving the raise sites:

```
1. Coerce ``field.choices`` to a list and reject if empty.
2. Reject Django's grouped-choices form.
3. Cache check on ``(field.model, field.name)``; return cached on hit.
4. Compute enum name ``f"{type_name}{PascalCase(field.name)}Enum"``.
5. Sanitize member names from choice *values* (not labels); reject if
   two values sanitize to the same identifier.
6. Build the ``Enum`` and decorate with ``strawberry.enum``.
7. Cache via ``registry.register_enum`` and return the enum class.
```

This mirrors the same comment-pass calibration as `rev-optimizer__plans.md`'s P1/P2/M1 anchor work and `rev-types__base.py`'s seven-step pipeline alignment.

### `convert_scalar` docstring `type_name` `Args:` entry under-documents the recursive ArrayField recursion

`converters.py:164-168` describes `type_name` as "Threaded through so the choice-enum path can build a stable `<TypeName><FieldName>Enum` GraphQL name." This is accurate for the ordinary scalar path but the ArrayField branch (`converters.py:205`) also threads `type_name` into the recursive `convert_scalar(field.base_field, type_name)` call so that an `ArrayField(CharField(choices=...))` produces an inner enum named per the OUTER ArrayField's `(model, base_field_name)` shape — not the synthetic `base_field` shape. The test `test_array_field_choices_inner_via_fake_sentinel` (`tests/types/test_converters.py:885`) pins the ENUM kind but does not pin the enum's NAME; the recursive-`type_name` plumbing is the load-bearing detail. Documenting it inside `Args:` would make the recursion-style contract greppable.

Recommended addition (one line):

```
type_name: The consumer-facing ``DjangoType`` class name. Threaded
    through so the choice-enum path can build a stable
    ``<TypeName><FieldName>Enum`` GraphQL name. Also threaded into
    the recursive ``base_field`` call on ``ArrayField``, so an inner
    choice-bearing element resolves under the outer field's name.
```

### `_sanitize_member_name` keyword/dunder/GraphQL-reserved rules interact in a non-obvious order; comment-pass to surface the ordering as load-bearing

The function at `converters.py:234-254` runs four sequential rewrites: (1) ASCII non-ident → `_`; (2) leading-digit / empty → `MEMBER_`; (3) Python keyword → `_<name>`; (4) GraphQL-reserved (`true`/`false`/`null`) OR `startswith("__")` → `MEMBER_<name>`. The interaction is correct (a Python keyword caught in step 3 produces `_if` which passes step 4; a GraphQL-reserved literal caught in step 4 still produces a unique result for sibling raw values) — but the docstring at `:235-246` summarises the rules out of execution order ("prefix with `MEMBER_` if the result starts with a digit … prefix with an underscore if it collides with a Python keyword. GraphQL-reserved enum values and introspection-prefixed names are also prefixed"). A reader walking the docstring then the body would not see why **GraphQL reserved is step 4 not step 1** until they hit the collision tests (`tests/types/test_converters.py:334`). The ordering is load-bearing: if step 4 ran first, `"MEMBER_true"` and `"true"` would still collide via the collision-detection downstream — same end behaviour but harder to reason about per-call.

Recommended fix: append one sentence to the docstring naming the execution order ("Rules apply in this order: …; the order is load-bearing because the keyword-and-reserved rewrites in steps 3 and 4 cannot collapse into a single condition without changing how downstream collision detection categorises ambiguous values.").

### `_resolve_array_field` / `_resolve_hstore_field` docstrings duplicate the same one-paragraph contract

Both helpers (`converters.py:89-99` and `:102-112`) repeat the same five-line summary ("Soft-import postgres `X`. Returns `None` if `django.contrib.postgres.fields` is unavailable so package import succeeds on dev environments without the postgres driver."). When the DRY analysis defer-with-trigger fires (third postgres-contrib soft-import landing), the consolidated helper's docstring would absorb both. Today the duplication is intentional sibling design (one-paragraph per function reads cleaner than a cross-reference), so no edit in scope — recorded under `### DRY recap > Duplication risk in the current file.` rather than as a forward.

## What looks solid

### DRY recap

- **Existing patterns reused.** `convert_scalar` (`converters.py:226`) delegates the MRO walk to the shared `scalar_for_field` helper (`converters.py:119-139`) which is the single field-class → scalar lookup also consumed by the filter-input converter (`filters/inputs.py::_scalar_from_model_field` at `filters/inputs.py:252-265`), so a column resolves to the same scalar on both sides of the package's converter / filter-input split — including consumer-registered `SCALAR_MAP` entries. `convert_choices_to_enum` (`converters.py:301-303`) reuses `registry.get_enum` / `register_enum` for the enum-cache layer, so the cache-vs-storage split lives in `registry.py` not here. `resolved_relation_annotation` (`converters.py:329-341`) reuses `FieldMeta.from_django_field` for cardinality / nullable rules so the relation-annotation logic shares the same shape with `optimizer/walker.py` and `types/finalizer.py`. The recursive `convert_scalar(field.base_field, type_name)` call at `converters.py:205` reuses the entire converter pipeline (choice substitution + null widening) on the inner element so the ArrayField branch is a thin outer-wrap-and-widen on top of the existing scalar path.
- **New helpers considered.** A `_postgres_branch(field, sentinel, ...)` extraction (see DRY analysis) was considered and rejected for the two-call-site footprint; the differing token (`list[inner]` synthesis vs `strawberry.scalars.JSON` return) and the field-shape-specific error message make the helper signature parameter-heavy without saving real bytes. A `_resolve_postgres_field(attr_name: str)` extraction was considered and rejected for the same reason — two sites is below the threshold and the explicit per-field naming keeps the monkeypatch test ergonomics greppable. A `_MEMBER_NAME_RULES` table was considered for `_sanitize_member_name` and rejected at three rules — readability wins inline.
- **Duplication risk in the current file.** The `_resolve_array_field` / `_resolve_hstore_field` paired body shape AND the `convert_scalar` ArrayField / HStoreField paired branch shape are intentional sibling design — the second site of each pair is load-bearing for symmetry of the postgres-contrib soft-import pattern, and the cross-method DRY consolidation triggers fire at the third-site landing per the DRY analysis bullets. Repeated `f"{field.model.__name__}.{field.name}"` error-message prefix across five raise sites (`:197`, `:201`, `:215`, `:280-281`, `:295`, `:320`) is the canonical Django-field error shape used throughout the package — duplicating the prefix here is cleaner than a `_field_qualname(field)` helper that would obscure the consumer-visible error grep target.

### Other positives

- **Sentinel-None short-circuit guards the `isinstance(field, _X_FIELD_CLS)` calls.** The `_ARRAY_FIELD_CLS is not None` and `_HSTORE_FIELD_CLS is not None` guards at `converters.py:194` and `:212` prevent `TypeError: isinstance() arg 2 must be a type` on dev environments without the postgres driver; both guards are pinned by `test_array_field_sentinel_none_path` (974) and `test_hstore_field_sentinel_none_path` (1240).
- **MRO walk dispatch is the canonical Django field extension path.** `scalar_for_field` walks `type(field).__mro__` so consumer-defined subclasses of `CharField` / `IntegerField` / etc. resolve to the parent's scalar without explicit `SCALAR_MAP` registration. Tests `test_convert_scalar_resolves_subclass_of_supported_field_to_parent_scalar` (366) and `test_convert_scalar_subclass_with_null_widens_through_mro_resolution` (385) pin the High-fix from a prior cycle; the latter even pins that the MRO-resolved scalar still flows through the `null=True` widening.
- **`DurationField` and `BinaryField` intentional absence is named in the module docstring.** The module docstring (`converters.py:25-32`) explicitly enumerates `DurationField` and `BinaryField` as intentionally absent from `SCALAR_MAP` and documents the consumer recourse (`SCALAR_MAP[DurationField] = MyDurationScalar`; `SCALAR_MAP[BinaryField] = strawberry.scalars.Base64`). Both are pinned by `test_convert_scalar_duration_field_raises_unsupported` (419) and `test_convert_scalar_binary_field_raises_unsupported` (442) with the same rationale text in the test docstring.
- **Choices-then-null ordering is documented as load-bearing.** `convert_scalar`'s algorithm doc (`converters.py:158-162`) explicitly states "Order matters: choices replaces `py_type` *before* null widening so nullable choice fields end up as `EnumType | None`, not `(str | None)` collapsed away." Test `test_choice_field_with_null_widens_to_enum_or_none` (256) pins the strict-equality form.
- **Grouped-choices detection on `label` not `value` is documented as load-bearing.** Inline comment block at `:286-292` calls out that in Django's grouped form the *value* slot is the human-readable group name (a string), so checking it would produce a false negative. The detection at `:293` lives on the right axis.
- **Choice enum members preserve DB values via `enum_cls.value`, not the sanitized member name.** `test_choice_field_generates_strawberry_enum` (119) pins `enum_cls.value` equals the raw DB string ("first-name", "123abc", "class") even though the GraphQL-side member name is sanitized — so the DB/wire boundary is stable across label edits.
- **`resolved_relation_annotation` is a thin three-line dispatch over `FieldMeta`.** `converters.py:336-341` delegates cardinality (`is_many_side` → `list[T]`) and nullability (`nullable` → `T | None`) to `FieldMeta.from_django_field`; same shape as the walker-side relation resolution and the finalizer's deferred-resolution path (`types/finalizer.py:219`). Documented in module docstring at `:13-17` with explicit cross-reference.
- **Cache lookup uses `(field.model, field.name)` keys per `registry.py`.** `convert_choices_to_enum` at `:301-303` and `:325` exclusively routes enum cache reads/writes through `registry.get_enum` / `register_enum`; no direct `_enums` dict manipulation. The first-`DjangoType`-wins-the-name contract is documented at `:270-272`.
- **GLOSSARY drift quick-check: clean.** The five backticked symbols from the dispatch (`convert_scalar`, `convert_choices_to_enum`, `convert_relation`, `Scalar field conversion`, `Specialized scalar conversions`) plus `scalar_for_field`, `resolved_relation_annotation`, and `SCALAR_MAP` cross-check against `docs/GLOSSARY.md` as follows: `Scalar field conversion` entry (`:976-1002`) lists every shipped scalar including the `BigInt` / `JSON` / `ArrayField` / `HStoreField` rows AND the consumer-subclass MRO walk AND the `DurationField` / `BinaryField` intentional absences AND the `null=True` widening — fully aligned. `Specialized scalar conversions` entry (`:1044-1056`) lists the five `0.0.6`-added rows (`BigIntegerField`, `PositiveBigIntegerField`, `JSONField`, `ArrayField`, `HStoreField`) — fully aligned with the SCALAR_MAP entries at `:54-81`. `Choice enum generation` (`:186-194`) correctly documents the `(model, field_name)` cache key, member-name sanitization from DB values, and grouped-choices rejection. `convert_scalar` / `convert_choices_to_enum` are correctly absent as public symbols (internal converter dispatch — consumer-visible behaviour surfaces through `Scalar field conversion` / `Choice enum generation` / `Specialized scalar conversions`); `convert_relation` is a historical symbol that was renamed to `resolved_relation_annotation` per `docs/SPECS/spec-018-meta_primary-0_0_6.md:139` ("the relation-annotation builder; was historically referenced as `convert_relation`") — `docs/TREE.md:214` and `:264` still cite the historical name in the per-file comment column; the latter is a `docs/TREE.md` hygiene issue that survives across this cycle (TREE drift is project-pass scope per `worker-1.md` "do not modify source/tests"). No in-cycle GLOSSARY edit warranted; forward `docs/TREE.md::converters.py` line column to project pass.

### Summary

`types/converters.py` is the 342-line scalar / choice-enum / relation-annotation conversion home. The module's logic is solid — sentinel-None postgres-field short-circuits guard the `isinstance` calls; the MRO walk delegates to a single shared `scalar_for_field` helper consumed by both `convert_scalar` (selected-field side) and `filters/inputs._scalar_from_model_field` (filter-input side) so a column resolves to the same scalar on both sides; choice substitution runs before null widening per a documented load-bearing rule pinned by strict-equality tests; recursive ArrayField processing reuses the entire `convert_scalar` pipeline on `base_field`; `resolved_relation_annotation` is a thin three-line `FieldMeta`-driven dispatch shared with the finalizer's deferred-resolution path. Zero High, zero Medium; five comment-pass Lows centered on `convert_choices_to_enum`'s `Raises:` block omitting the documented sanitized-member-collision raise (most consequential), the numbered-step docstring eliding two of its own raise paths, the `convert_scalar` `type_name` `Args:` entry under-documenting the recursive ArrayField recursion, the `_sanitize_member_name` ordering-as-load-bearing comment, and the paired `_resolve_array_field` / `_resolve_hstore_field` docstring duplication. Three defer-with-explicit-trigger DRY items (paired postgres-field resolvers; paired sentinel-guarded `convert_scalar` branches; `_sanitize_member_name` rewrite-rule table) all gate on a third-site landing in the same shape pattern. GLOSSARY drift quick-check clean for the five named symbols. Standard three-spawn cycle — five Lows all require real source edits at comment-pass time. `Status: under-review`.

---

## Fix report (Worker 2)

Consolidated single-spawn pass — all five Lows are docstring-only per artifact recommendations; logic + comment + changelog disposition collapsed into one spawn (shape #4).

### Files touched

- `django_strawberry_framework/types/converters.py::convert_scalar #"type_name: The consumer-facing"` — Low #3: appended one sentence to the `type_name` `Args:` entry documenting that `type_name` is also threaded into the recursive `base_field` call on `ArrayField` so inner choice-bearing elements resolve under the outer field's name.
- `django_strawberry_framework/types/converters.py::_sanitize_member_name` — Low #4: appended one paragraph naming the four-step execution order and labelling it load-bearing (keyword and reserved rewrites in steps 3 and 4 cannot collapse into a single condition without changing downstream collision categorisation).
- `django_strawberry_framework/types/converters.py::convert_choices_to_enum` — Low #2: rewrote the numbered-step list from 7 steps to 7 faithful steps that interleave the two raise sites (empty-choices reject at step 1, grouped-choices reject at step 2, collision reject at step 5); Low #1: extended the `Raises:` block from a flat one-sentence form to a three-sub-bullet enumeration mirroring `convert_scalar`'s `Raises:` style, naming the empty-choices, grouped-choices, and sanitized-member-collision paths.
- Low #5 (`_resolve_array_field` / `_resolve_hstore_field` duplicated one-paragraph docstrings): no edit per the artifact's own prose ("recorded under `### DRY recap > Duplication risk in the current file.` rather than as a forward") — the duplication is intentional sibling design and the consolidation triggers at the third postgres-field soft-import landing.

### Tests added or updated

None. All five Lows are docstring-only — Worker 1's artifact explicitly framed the Raises: omission, numbered-step rewrite, recursive ArrayField recursion note, and ordering load-bearing sentence as comment-pass calibration. The cited regression tests (`test_convert_choices_to_enum_raises_on_sanitized_member_collision` at `test_converters.py:293`, `::test_convert_choices_to_enum_raises_on_keyword_prefix_collision` at `:314`, `::test_convert_choices_to_enum_raises_on_graphql_safe_name_collision` at `:334`, `test_array_field_choices_inner_via_fake_sentinel` at `:885`, `test_array_field_sentinel_none_path` at `:974`, `test_hstore_field_sentinel_none_path` at `:1240`) already pin the underlying contracts the docstrings now document; no test surface needs an update.

### Validation run

- `uv run ruff format .` — pass, 212 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed.
- pytest not run per dispatch instruction and AGENTS.md #14.

### Notes for Worker 3

- No shadow file was used; the source-file line numbers cited above are original.
- All edits are inside docstrings of `convert_scalar`, `_sanitize_member_name`, and `convert_choices_to_enum`. The numbered-step rewrite + `Raises:` extension for `convert_choices_to_enum` follows the exact recommended text in the artifact (Low #1 + Low #2 fix blocks) and mirrors `convert_scalar`'s `Raises:` enumeration style. The `_sanitize_member_name` ordering paragraph echoes the artifact's recommended sentence template ("Rules apply in this order: …; the order is load-bearing because…").
- `git status` at task start shows many concurrent maintainer paths dirty across `django_strawberry_framework/`, `tests/`, `examples/fakeshop/`, `docs/`, `scripts/`; treated as out-of-scope per AGENTS.md #33 and left untouched.
- `uv.lock` not touched.

---

## Comment/docstring pass

Consolidated into the Fix report above (single-spawn pass).

### Files touched

See `## Fix report (Worker 2) > ### Files touched` above — the same docstring edits constitute both the logic and the comment pass since all five Lows are docstring-only.

### Per-finding dispositions

- Low #1 (`convert_choices_to_enum` `Raises:` omits sanitized-member-collision): **applied verbatim per artifact recommended text** — three-sub-bullet `Raises:` block mirroring `convert_scalar`'s style; bullets cover empty-choices, grouped-choices, and sanitized-member-collision paths with the artifact's `"a-b"` / `"a_b"` collision example preserved.
- Low #2 (numbered-step list elides empty-choices and collision raises): **applied verbatim per artifact recommended text** — 7-step list now interleaves the two raise sites (step 1 names the empty-choices reject; step 5 names the collision reject).
- Low #3 (`convert_scalar` `type_name` `Args:` under-documents recursive ArrayField recursion): **applied verbatim per artifact recommended text** — one-line addition to the `Args:` entry naming the recursive `base_field` threading and the outer-field-name contract.
- Low #4 (`_sanitize_member_name` ordering as load-bearing): **applied per artifact recommended sentence template** — appended one paragraph naming the four-step order and the load-bearing rationale (steps 3 and 4 cannot collapse without changing downstream collision detection).
- Low #5 (paired `_resolve_array_field` / `_resolve_hstore_field` docstring duplication): **no in-cycle edit** per the artifact's own prose ("no edit in scope — recorded under `### DRY recap > Duplication risk in the current file.` rather than as a forward"). Intentional sibling design pending the third postgres-field soft-import landing per DRY analysis trigger.

### Validation run

- `uv run ruff format .` — pass, 212 files left unchanged.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

Comment pass consolidated with the logic pass; same file changes serve both. No additional notes.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Cite both halves per worker-2.md rule:

- **AGENTS.md #21**: "Do not update CHANGELOG.md unless explicitly instructed."
- **Active plan silence**: the dispatch prompt explicitly states "Changelog `Not warranted` (docstring polish only) citing AGENTS.md + active plan silence" — the active plan does not authorize a CHANGELOG edit for this cycle.

The cycle's edits are documentation-only: three docstrings tightened to faithfully describe behaviour that is already shipped, already pinned by regression tests, and already documented in `docs/GLOSSARY.md` (`Scalar field conversion`, `Specialized scalar conversions`, `Choice enum generation`). Zero source-behaviour change, zero public-API surface change, zero typed-error contract change — calibrates cleanly to "internal-only refactors against docstring polish" per the `Not warranted` definition in `worker-2.md`. Comparable prior calibration: `exceptions.py` (docstring rewrite dropping a non-existent path), `list_field.py` (citation + docstring rotation), `testing/_wrap.py` (pure docstring polish on a single public symbol). All landed as `Not warranted`.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass, 212 files left unchanged.
- `uv run ruff check --fix .` — pass.

---

---

## Verification (Worker 3)

### Logic verification outcome

All five Lows resolved per artifact recommendations. Low #1 `Raises:` block extended at `converters.py:287-297` to three sub-bullets covering empty-choices, grouped-choices, and the sanitized-member-collision path (preserves the artifact's `"a-b"` / `"a_b"` collapse example verbatim, mirrors `convert_scalar`'s `Raises:` enumeration style). Low #2 numbered-step list rewritten at `converters.py:273-281` from 7 steps to 7 steps that interleave the raise sites — step 1 names the empty-choices reject, step 5 names the collision reject (matches recommended block char-for-char). Low #3 `convert_scalar` `type_name` `Args:` entry extended at `converters.py:166-171` with the one-line recursive-`base_field` threading note (verbatim per artifact). Low #4 `_sanitize_member_name` ordering paragraph appended at `converters.py:250-258` naming the four-step execution order and labelling it load-bearing (matches the artifact's recommended sentence template). Low #5 (paired `_resolve_array_field` / `_resolve_hstore_field` docstring duplication) intentionally untouched per the artifact's own prose ("no edit in scope — recorded under `### DRY recap > Duplication risk in the current file.` rather than as a forward"); deferral to the third postgres-field soft-import landing holds.

### DRY findings disposition

All three DRY analysis items remain defer-with-explicit-trigger: (a) `_resolve_array_field` + `_resolve_hstore_field` → `_resolve_postgres_field(attr_name)` collapse waits on the third postgres-contrib field landing (`CIText`, range fields); (b) `_postgres_branch` helper extraction across the ArrayField / HStoreField branches of `convert_scalar` waits on the third sentinel-guarded postgres-field branch; (c) `_MEMBER_NAME_RULES` table-driven `_sanitize_member_name` rewrite waits on a fourth rewrite rule. All three triggers are grep-discoverable and the artifact's rationale (two-site footprint below the extraction threshold; load-bearing differing tokens for monkeypatch test ergonomics) holds.

### Temp test verification

No temp tests created. All edits are docstring-only; the cited regression tests (`test_convert_choices_to_enum_raises_on_sanitized_member_collision` at `tests/types/test_converters.py:293`, `::test_convert_choices_to_enum_raises_on_keyword_prefix_collision` at `:314`, `::test_convert_choices_to_enum_raises_on_graphql_safe_name_collision` at `:334`, `test_array_field_choices_inner_via_fake_sentinel` at `:885`, `test_array_field_sentinel_none_path` at `:974`, `test_hstore_field_sentinel_none_path` at `:1240`) already pin the contracts the docstrings now document. No focused pytest run needed; the docstring edits do not move any source-logic line.

### Verification outcome

`cycle accepted; verified`

- `git diff -- django_strawberry_framework/types/converters.py` shows three docstring-only hunks scoped to `convert_scalar` `Args:`, `_sanitize_member_name`, and `convert_choices_to_enum`.
- `git diff -- CHANGELOG.md` empty; changelog disposition `Not warranted` cites both AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and active-plan silence in `review-0_0_7.md`.
- `uv run ruff format --check django_strawberry_framework/types/converters.py` → `1 file already formatted`.
- `uv run ruff check django_strawberry_framework/types/converters.py` → `All checks passed!`.

---

## Iteration log
