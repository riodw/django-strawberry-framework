# Review: `django_strawberry_framework/types/base.py`

Status: verified

## DRY analysis

- Defer until a second `Meta.*` key joins the bool family (i.e. a second boolean-shape Meta attribute beyond `primary`): extract a single `_meta_value(meta, key, default)` helper to consolidate the five `getattr(meta, "...", default)` reads at `types/base.py:164` (`primary`), `:221` (`name`), `:222` (`description`), `:223` (`fields`), `:224` (`exclude`). Value is mostly a typed-shape gate, not a line-count win.
- Thread `primary` back through `_validate_meta`'s return value (the same shape `interfaces` already uses): `primary = getattr(meta, "primary", False)` is currently read once at `base.py:164` for type validation and re-read at `base.py:528` for use, while `interfaces` is threaded back via the return value. Aligning the two would close a minor asymmetry in the `_validate_meta` contract.

## High:

None.

## Medium:

### Reflective re-read of `primary` diverges from the `interfaces` pattern

`_validate_meta` validates `primary` shape at `types/base.py:528-530` but discards the value; `__init_subclass__` re-reads it via raw `getattr` at line 164 and re-reads it AGAIN at line 235 (passed to `DjangoTypeDefinition(... primary=primary)`). Compare against `interfaces`, where `_validate_meta` returns the validated tuple at line 546 and the caller consumes that return value through `__init_subclass__` (line 158) into both `_build_annotations` (line 216) and `DjangoTypeDefinition.interfaces` (line 234). The asymmetry creates two failure-mode risks: (a) a future maintainer adding a third validated Meta bool will not have a pattern to follow — `interfaces` says "thread the validated value back", `primary` says "re-read raw"; (b) the `primary` re-read uses the same `getattr(meta, "primary", False)` shape as the raw read inside `_validate_meta`, so if anything in `_validate_meta` mutates `meta.primary` (e.g. a hypothetical normalizer that coerces truthy non-bool to bool before the type check), the two reads will disagree silently. Recommended change: have `_validate_meta` return `(interfaces, primary)` (or a small named tuple), and have `__init_subclass__` consume the returned `primary` instead of re-reading. Single-pass validation pattern; matches the `interfaces` shape that already exists in the same file.

```django_strawberry_framework/types/base.py:158-164
        interfaces = _validate_meta(meta)
        fields = _select_fields(meta)
        _validate_optimizer_hints(meta, fields)

        field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}
        optimizer_hints = _meta_optimizer_hints(meta)
        primary = getattr(meta, "primary", False)
```

```django_strawberry_framework/types/base.py:526-546
    if "fields" in declared and "exclude" in declared:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    primary = getattr(meta, "primary", False)
    if not isinstance(primary, bool):
        raise ConfigurationError("Meta.primary must be a bool")

    deferred = sorted(declared & DEFERRED_META_KEYS)
    ...
    _normalize_fields_spec(getattr(meta, "fields", None))
    _normalize_sequence_spec(getattr(meta, "exclude", None))
    _meta_optimizer_hints(meta)

    return _validate_interfaces(meta)
```

### `_meta_optimizer_hints` is invoked three times per class creation

`_meta_optimizer_hints` runs the same `getattr` + `isinstance(Mapping)` + `dict(...)` pipeline at three sites in a single `__init_subclass__` pass: line 163 (capture for `DjangoTypeDefinition.optimizer_hints`), line 544 inside `_validate_meta` (shape-only validation; return value discarded), and line 566 inside `_validate_optimizer_hints` (re-fetch for key/value validation). The three calls allocate three independent dicts from the same `meta.optimizer_hints` source. The cost is small (class-creation-time, dict size = number of optimizer hints), but the redundancy is the actual issue: a future maintainer adding a fourth gate (e.g., per-key value-shape validation) might add a fourth call rather than thread the dict through. Recommended change: compute `optimizer_hints_dict = _meta_optimizer_hints(meta)` once inside `_validate_meta`, return it alongside `interfaces` (paired with the `primary` thread-through above), and consume the returned dict in both `__init_subclass__` (line 163) and `_validate_optimizer_hints` (line 566). Single-pass shape; matches the `interfaces` thread-through pattern already in the file.

```django_strawberry_framework/types/base.py:540-546
    _normalize_fields_spec(getattr(meta, "fields", None))
    _normalize_sequence_spec(getattr(meta, "exclude", None))
    _meta_optimizer_hints(meta)

    return _validate_interfaces(meta)


def _validate_optimizer_hints(meta: type, fields: tuple[Any, ...]) -> None:
```

```django_strawberry_framework/types/base.py:565-568
    """
    hints = _meta_optimizer_hints(meta)
    if not hints:
        return
```

### `__init_subclass__` complexity remains a Medium-tier hotspot

The static helper flagged `DjangoType.__init_subclass__` at 98 lines and 9 branch nodes (overview lines 53-60), well above the 40-line / 8-branch hotspot threshold. The function is the consumer-facing contract entrypoint for `DjangoType` and orchestrates seven distinct phases (custom-get_queryset detection, Meta detection, finalized-registry guard, Meta validation, field selection, optimizer-hint validation, consumer-authored-field collection, Relay id-collision guards, annotation synthesis, definition construction, registry write, pending-relation registration, annotation merge, is_type_of install). Each phase is individually correct and reachable from the existing test surface, but the linear shape makes the function hard to follow for a new maintainer and discourages the kind of single-pass thread-through refactor proposed in the two findings above. Recommended change: extract a `_collect_consumer_authored_fields(cls, fields) -> tuple[frozenset[str], dict[str, frozenset[str]]]` helper that owns lines 165-183 (the four-corner override collection); extract `_assert_no_relay_id_collision(cls, relay_shaped)` for lines 184-209 (the H1 collision guard). Both extractions move the high-branch-count work out of `__init_subclass__`'s top-level body without changing call semantics. Defer until the `primary` thread-through above lands so the two refactors compose.

```django_strawberry_framework/types/base.py:145-242
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect model/type metadata without finalizing the Strawberry type."""
        super().__init_subclass__(**kwargs)
        has_custom_get_queryset = _detect_custom_get_queryset(cls)
        cls._is_default_get_queryset = not has_custom_get_queryset
        ...
        install_is_type_of(cls)
```

## Low:

### `consumer_annotations` is captured with `getattr` while two later reads use direct attribute access

Line 165 uses `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` with a defensive `{}` default, but lines 187 (`"id" in cls.__annotations__`) and 240 (`cls.__annotations__ = {**synthesized, **consumer_annotations}`) reference `cls.__annotations__` directly. In Python ≥3.10 (pyproject pins `>=3.10,<4.0`) every class gets its own `__annotations__` dict on attribute access, so the defensive default at line 165 is dead — and the three reads should use the same shape. Recommended change: drop the `getattr(...)` wrapper at line 165 in favor of `cls.__annotations__`, OR (if defensive coding is wanted) propagate the `getattr` to lines 187 and 240. Cosmetic consistency only; behavior identical on supported Python versions.

```django_strawberry_framework/types/base.py:165-187
        consumer_annotations = dict(getattr(cls, "__annotations__", {}))
        consumer_annotated_relation_fields = frozenset(
            field.name for field in fields if field.is_relation and field.name in consumer_annotations
        )
        ...
            has_id_annotation = "id" in cls.__annotations__
```

### `_record_pending_relation` is a one-shot wrapper

`_record_pending_relation` at `types/base.py:793-808` is a 16-line wrapper (including docstring) with a single call site at `_build_annotations:772`. The wrapper threads `cls, source_model, field, field_meta` into a `PendingRelation(...)` constructor that takes seven positional kwargs. Inlining at the call site would be three lines and saves the indirection. Recommended change: inline at line 772 (the field_map lookup and `field_meta` are already local at that scope), or leave as-is if the call surface is expected to grow.

```django_strawberry_framework/types/base.py:793-808
def _record_pending_relation(
    cls: type,
    source_model: type[models.Model],
    field: Any,
    field_meta: FieldMeta,
) -> PendingRelation:
    """Build a pending relation record from a selected Django relation field."""
    return PendingRelation(
        source_type=cls,
        source_model=source_model,
        field_name=field.name,
        django_field=field,
        related_model=field.related_model,
        relation_kind=field_meta.relation_kind,
        nullable=field_meta.nullable,
    )
```

### `_normalize_fields_spec` / `_normalize_sequence_spec` re-walk the path three times

`_normalize_fields_spec(getattr(meta, "fields", None))` is invoked at lines 542 (validation in `_validate_meta`), 627 (inside `_select_fields`), and 223 (inside the `DjangoTypeDefinition(...)` constructor call at `__init_subclass__`). `_normalize_sequence_spec` follows the same pattern with two of the three sites. Each invocation is pure, idempotent, and runs at class-creation time, so this is not a runtime defect — but the pattern shouts "thread the value through". Bundle with the `primary` / `optimizer_hints_dict` thread-through proposal in the Medium findings: have `_validate_meta` return the normalized specs and consume them at the `_select_fields` and `DjangoTypeDefinition` sites.

```django_strawberry_framework/types/base.py:222-225
            description=getattr(meta, "description", None),
            fields_spec=_normalize_fields_spec(getattr(meta, "fields", None)),
            exclude_spec=_normalize_sequence_spec(getattr(meta, "exclude", None)),
            selected_fields=tuple(fields),
```

### `cls._is_default_get_queryset` is stamped on classes that will be rejected by the `registry.is_finalized()` guard

`__init_subclass__` calls `_detect_custom_get_queryset(cls)` at line 148 and stamps `cls._is_default_get_queryset` at line 149 BEFORE the `if meta is None: return` short-circuit (line 151-152) AND before the `registry.is_finalized()` rejection at line 153-157. A class that is going to be rejected by the finalized-registry guard still gets the boolean stamped. Practical impact is nil — the rejected class is never registered and is unreachable from finalized type lookups — but if any test fixture or registry cleanup path inspects `cls._is_default_get_queryset` on a class that failed registration, the stamped value would persist on the failing class. Defer the stamp until after both early-return / raise checks. Cosmetic ordering only.

```django_strawberry_framework/types/base.py:145-157
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect model/type metadata without finalizing the Strawberry type."""
        super().__init_subclass__(**kwargs)
        has_custom_get_queryset = _detect_custom_get_queryset(cls)
        cls._is_default_get_queryset = not has_custom_get_queryset
        meta = cls.__dict__.get("Meta")
        if meta is None:
            return
        if registry.is_finalized():
            raise ConfigurationError(
                f"finalize_django_types() already ran; cannot register {cls.__name__} "
                "after finalization. Call registry.clear() first if this is a test.",
            )
```

### `_validate_interfaces` docstring still cites "Slice 4's Phase 2.5" and "0.0.5" while the package is at 0.0.6

The docstring at `types/base.py:438-462` references `0.0.5` in two places ("Lazy/forward-reference interface lookup is out of scope for 0.0.5" at line 461; "Slice 4's Phase 2.5" at line 437). The `__init__.py` and `pyproject.toml` are at `0.0.6`. The stale version-stamp does not change behavior (the constraint is still in effect; the spec did not promote lazy lookup in 0.0.6), but the cross-reference reads as referring to a shipped release whose semantics carried forward. Comment-pass fix: replace "for 0.0.5" with "in this release" or leave the constraint phrased without a version label. Same review-cycle observation as the version-anchor calibration noted in `worker-memory/worker-1.md` for `conf.py`: stale version stamps are Low until they outlive the spec they reference.

```django_strawberry_framework/types/base.py:437-462
    The composite-pk constraint and ``relay.Node`` MRO inspection live
    in Slice 4's Phase 2.5; this helper only validates the shape and
    contents of the ``Meta.interfaces`` tuple itself.
    ...
                f"not strings (got {entry!r}). Lazy/forward-reference interface lookup is "
                "out of scope for 0.0.5.",
            )
```

## What looks solid

### DRY recap

- **Existing patterns reused.** `_format_unknown_fields_error` at `types/base.py:390-398` is the canonical formatter for `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` unknown-name errors, consumed at four sites in this file (`types/base.py:576-582,586-592,640-646,652-658`) and explicitly cross-referenced by `types/finalizer.py:25-28` so the sibling-formatter contract stays in sync. `_interfaces_shape_error` at `types/base.py:406-413` localizes the two shape-rejection raise sites at `types/base.py:445,451`. `_is_relay_shaped` at `types/base.py:126-137` is the single-sited Relay-Node predicate consumed at `types/base.py:184` (collision guard) and `types/base.py:740` (`_build_annotations` pk-suppression branch); its docstring explicitly documents the two-call-site contract. `_meta_optimizer_hints` at `types/base.py:372-387` funnels the non-mapping shape rejection through one site for three callers (`base.py:163,544,566`). `_id_annotation_is_relay_node_id`'s fail-soft regex helper `_NODEID_STRING_RE` at `types/base.py:72` is the only Strawberry-collateral string surface in the file. Helper `_normalize_fields_spec` (`base.py:291-297`) and `_normalize_sequence_spec` (`base.py:300-306`) own the shape gates for `Meta.fields` / `Meta.exclude`, called from both `_validate_meta` (lines 542-543) and `_select_fields` (lines 627-628). `_consumer_assigned_fields` (`base.py:309-369`) is the sole-source for the four-corner consumer-override contract feeding `DjangoTypeDefinition` and `_build_annotations`; documented at `base.py:313-350`. Test pinning lives at `tests/types/test_definition_order.py:211-323,575-784` and `tests/types/test_converters.py:1516-1550`.
- **New helpers considered.** A `_consumer_annotations_by_branch(consumer_annotations, fields)` helper would consolidate the two parallel comprehensions at `base.py:166-171` (relation + scalar splits walk the same `fields` tuple twice with the same `field.name in consumer_annotations` test) into one O(N) pass returning a `(relation_set, scalar_set)` tuple — same shape as `_consumer_assigned_fields` returns. Low-priority polish; the two passes are short and execute once at class-creation time.
- **Duplication risk in the current file.** Line 165 reads `getattr(cls, "__annotations__", {})` defensively; lines 187 and 240 read `cls.__annotations__` directly. The inconsistency is bounded — Python ≥3.10 (pyproject `requires-python = ">=3.10"`) makes both shapes equivalent for any class with a Meta block — but the pattern reads as drift. `_meta_optimizer_hints(meta)` is called three times per `__init_subclass__` invocation (lines 163, 544, 566); each call re-allocates the dict. `_normalize_fields_spec(getattr(meta, "fields", None))` runs three times in the path (line 542 inside `_validate_meta`, line 627 inside `_select_fields`, line 223 inside the `DjangoTypeDefinition` constructor); `_normalize_sequence_spec` runs twice (lines 543 and 628). Each call is pure and idempotent and only at class-creation time, so the duplication is Low impact but reads as redundant validation.

### Other positives

- Static helper ran cleanly; the file is 808 lines with 7 control-flow hotspots and a dense Django/ORM marker table. Every helper has a docstring describing the intended behavior and the cross-module contract it participates in (`_is_relay_shaped` explicitly names its two call sites; `_consumer_assigned_fields` documents the four-corner override matrix; `_meta_optimizer_hints` calls out the three-site funnel).
- The four-corner consumer-override contract (`consumer_annotated_relation_fields`, `consumer_annotated_scalar_fields`, `consumer_assigned_relation_fields`, `consumer_assigned_scalar_fields`) is fully test-pinned at `tests/types/test_definition_order.py:211-784`, including the `shadows a Django relation/scalar field` rejection paths at both branch sites.
- The Relay `id` collision guard at `types/base.py:184-209` correctly distinguishes assigned-`StrawberryField` (line 186 — always rejected with a long actionable message that names every escape hatch) from annotated-only (line 202 — accepted iff `_id_annotation_is_relay_node_id` returns True). The fail-soft string-regex fallback in `_id_annotation_is_relay_node_id` (`base.py:72,116-122`) is pinned by the prefixed-substring rejection tests at `tests/types/test_definition_order.py:611-629,642-720`.
- `_is_relay_shaped` is the single source of truth for "would `relay.Node` be in this type's MRO post-finalization", with explicit docstring discipline calling out its two call sites; matches the `extension.py` calibration carried in worker-1 memory.
- The `_validate_meta` ordering — `model` shape, then `fields`/`exclude` exclusivity, then `primary` type check, then deferred keys, then unknown keys, then per-key shape gates, then `interfaces` validation — produces deterministic error messages for each shape mismatch and is fully test-pinned at `tests/types/test_base.py:120-273,320-396`.
- `_build_annotations` correctly suppresses the pk scalar annotation only when `_is_relay_shaped` is True and the field's `name` matches the model's `_meta.pk.name` (not `pk_attname`); the docstring at `base.py:741-748` calls out the relation-pk edge case explicitly (`OneToOneField(primary_key=True)` where `name != attname`) and explains why naming the local `pk_attname` would be a maintainer trap.
- `_select_fields` is called once per `__init_subclass__` and the result is reused by `_build_annotations` and `_attach_relation_resolvers` (per the docstring at `base.py:604-610`), so `model._meta.get_fields()` runs exactly once per class definition rather than twice.
- The deferred keys / allowed keys frozensets at `base.py:48-69` match the spec-014 promotion of `primary` into `ALLOWED_META_KEYS` and the `_validate_meta` typo guard at line 538-540 rejects unknown declared keys with the model name + key list.

### Summary

`types/base.py` is the consumer-facing collection-pipeline entrypoint for `DjangoType`; the file is dense (808 lines) but the helpers are well-named, single-purpose, and each carries a docstring explaining its participation in the cross-module contract. Three Medium findings cluster around the same pattern: `_validate_meta` already returns the validated `interfaces` tuple, but the parallel `primary` bool and the `_meta_optimizer_hints` dict are NOT threaded back, so `__init_subclass__` re-reads them via raw `getattr`. Bundling the thread-through with a small `__init_subclass__` extraction (`_collect_consumer_authored_fields`, `_assert_no_relay_id_collision`) would reduce the 98-line / 9-branch hotspot without changing behavior. Lows are polish: a one-shot wrapper that could be inlined, three repeated `_normalize_fields_spec` calls along the same path, an inconsistent `getattr` vs direct read on `cls.__annotations__`, an ordering nit on `cls._is_default_get_queryset` stamping, and a stale `0.0.5` version stamp in `_validate_interfaces`'s docstring. The four-corner consumer-override contract and the Relay `id` collision guard are both clean, well-documented, and fully test-pinned.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py`:
  - M1 + M2 + L3 thread-through: added `_ValidatedMeta` NamedTuple (`types/base.py:493-507`); rewrote `_validate_meta` (`types/base.py:510-575`) to compute `interfaces`, `primary`, `optimizer_hints`, `fields_spec`, and `exclude_spec` once and return them as the snapshot tuple; rewrote `_validate_optimizer_hints` (`types/base.py:578-637`) signature to `(hints: dict[str, Any], fields: tuple[Any, ...]) -> None`, deriving the model from `fields[0].model` so the precomputed hints dict is consumed directly; updated `__init_subclass__` to bind `validated = _validate_meta(meta)` (`types/base.py:165`) and consume `validated.primary`, `validated.optimizer_hints`, `validated.fields_spec`, `validated.exclude_spec`, and `validated.interfaces` at the `_validate_optimizer_hints` call (`types/base.py:167`), the relay-shape check (`types/base.py:189`), the `_build_annotations` call (`types/base.py:218`), and the `DjangoTypeDefinition` construction (`types/base.py:222-241`).
  - L1 `__annotations__` consistency: changed `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` to `consumer_annotations = dict(cls.__annotations__)` at `types/base.py:170`.
  - L2 inline `_record_pending_relation`: inlined the `PendingRelation(...)` constructor at the single call site in `_build_annotations` (`types/base.py:801-811`); deleted the `_record_pending_relation` helper from the bottom of the file.
  - L4 NOT applied (see "Notes for Worker 3"); added an anchor comment at the stamp site (`types/base.py:153-159`) documenting the ordering invariant the test pins.

### Tests added or updated

- None. The refactor is internally observable only; existing tests pin the behavior and continue to pass (`tests/types/test_base.py`, 58 tests).

### Validation run

- `uv run ruff format .` — pass (no changes after the final pass).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv run pytest tests/types/test_base.py -x` — pass (58 tests passed).

### Notes for Worker 3

- **L4 not applied — test pins the original ordering.** The artifact's L4 proposed moving the `cls._is_default_get_queryset = not has_custom_get_queryset` stamp AFTER the `meta is None` early-return and the `registry.is_finalized()` raise. Existing test `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_abstract_base_without_meta` (the docstring at `tests/types/test_base.py:560-579` explicitly calls out the "abstract base without Meta" pattern and labels the deferred-stamp shape a former P1 bug) requires the stamp to happen BEFORE the `meta is None` early-return so an abstract base that overrides `get_queryset` without declaring Meta still flips the flag for concrete subclasses inheriting from it. Initial attempt to apply L4 broke that test; reverted and added an anchor comment naming the invariant and the test that pins it (`types/base.py:153-159`). The artifact's "Practical impact is nil" justification missed this consumer-supported pattern.
- **M3 deferred to follow-up cycle.** Per the artifact's own deferral note, the `_collect_consumer_authored_fields` and `_assert_no_relay_id_collision` extractions are substantial and were deferred to compose with the now-landed thread-through. Recording the deferral here so the project pass can track the carry-forward; not in scope for this cycle.
- **L5 deferred to comment pass.** Stale `0.0.5` docstring references in `_validate_interfaces` (lines 437, 461) belong in the comment pass per worker-2 memory's logic-first / comments-second discipline.
- **Signature change for `_validate_optimizer_hints`.** New signature `(hints: dict[str, Any], fields: tuple[Any, ...])`. The model is derived from `fields[0].model` — `_select_fields` always returns at least the pk field (a forward field whose `.model` is the source model) under realistic Meta declarations, so the lookup is safe across the existing test surface. If an edge case ever surfaces where `fields` could be empty with `hints` non-empty, the function would `IndexError` before raising the expected `ConfigurationError`; not currently reachable via the public Meta surface.
- No shadow file was used during this fix.

---

## Verification (Worker 3)

### Logic verification outcome

- **High:** None — accepted (no High findings).
- **M1 + M2 + L3 (`_ValidatedMeta` thread-through):** accepted. `_ValidatedMeta` NamedTuple defined at `types/base.py:496-510` with the five required fields (`interfaces`, `primary`, `optimizer_hints`, `fields_spec`, `exclude_spec`); `_validate_meta` returns the snapshot at `types/base.py:570-576`; `__init_subclass__` binds `validated = _validate_meta(meta)` at line 164 and consumes `validated.primary` / `validated.optimizer_hints` / `validated.fields_spec` / `validated.exclude_spec` / `validated.interfaces` at the call sites (lines 166, 188, 220, 227-228, 231, 238-239, 241). No re-read of `getattr(meta, "primary", ...)`, no re-call of `_meta_optimizer_hints(meta)`, no re-call of `_normalize_fields_spec` / `_normalize_sequence_spec` at the `DjangoTypeDefinition` site. `_validate_optimizer_hints` signature now `(hints: dict[str, Any], fields: tuple[Any, ...]) -> None` at `types/base.py:579` and consumes the precomputed dict at line 604 with the model derived from `fields[0].model` at line 606.
- **M3 (`__init_subclass__` extractions):** deferred to follow-up review cycle — accepted. Carry-forward recorded for the project pass; the artifact's own deferral note frames the extractions as composing with the now-landed thread-through.
- **L1 (`cls.__annotations__` direct access):** accepted. `consumer_annotations = dict(cls.__annotations__)` at `types/base.py:169` (no defensive `getattr`).
- **L2 (`_record_pending_relation` inlined):** accepted. Helper deleted; single call site at `_build_annotations` now constructs `PendingRelation(...)` directly with the seven kwargs at `types/base.py:809-818`. `grep -n "_record_pending_relation" types/base.py` returns zero matches.
- **L4 (`cls._is_default_get_queryset` stamp ordering):** reverted by Worker 2 — accepted. Verified by reading `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_abstract_base_without_meta` at lines 556-589: an abstract base that overrides `get_queryset` without declaring Meta must still flip `_is_default_get_queryset` (the test's docstring at lines 557-568 explicitly labels the deferred-stamp shape a former P1 bug). The stamp ordering at `types/base.py:154-155` is correctly preserved BEFORE the `meta is None` early return; an anchor comment at lines 148-153 names the invariant and the pinning test. The artifact's "Practical impact is nil" justification missed the consumer-supported abstract-base pattern; Worker 2's revert is the right decision.
- **L5 (stale `0.0.5` docstring):** deferred to comment pass — accepted per logic-first / comments-second discipline.

`_meta_optimizer_hints` call-site audit: `grep -n "_meta_optimizer_hints" types/base.py` returns one definition (line 376) plus one call (line 567 inside `_validate_meta`). Three call sites collapsed to one as required.

`_select_fields` is intentionally unchanged at `types/base.py:664-665` (the artifact-acknowledged separate-scope `_normalize_fields_spec` / `_normalize_sequence_spec` calls inside the selection helper).

Diff scope confirmed: `git diff -- django_strawberry_framework/types/base.py` is the only cycle-scoped delta; the other modified files in the working tree are uncommitted prior-cycle artifacts (per worker-memory calibration on folder-pass diff-vs-HEAD growth).

### DRY findings disposition

Three Mediums (M1 + M2 plus the L3 normalize-spec re-walk) collapsed via one thread-through refactor; `_validate_meta` is now the single normalization gate inside `__init_subclass__`, threading the validated `interfaces` / `primary` / `optimizer_hints` / `fields_spec` / `exclude_spec` back via the `_ValidatedMeta` NamedTuple. M3 (`_collect_consumer_authored_fields` and `_assert_no_relay_id_collision` extractions) deferred with carry-forward to the project pass. L5 (stale `0.0.5` docstring stamp) deferred to the comment pass. Accepted.

### Temp test verification

None. The existing test surface (`tests/types/test_base.py`, 58 tests) pins the behavior end-to-end; `uv run pytest tests/types/test_base.py -x` passes locally (58 passed in 0.18s).

### Verification outcome

`logic accepted; awaiting comment pass`. Top-level `Status:` not advanced (remains `fix-implemented` for Worker 2's next pass on comments).

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/types/base.py`:
  - **L5 — `_validate_interfaces` docstring + error-message version stamps:** replaced "Slice 4's Phase 2.5" with "``finalize_django_types()`` (Relay finalization phase)" at `types/base.py:441-444` (docstring body); replaced "out of scope for 0.0.5" with "deferred (no current spec home)" in the error message at `types/base.py:465`. Constraint wording ("Lazy/forward-reference interface lookup is …") preserved verbatim; only the version stamp / spec anchor changed. GLOSSARY.md does not list lazy/forward-reference interface lookup as a planned feature, so the new wording names no future spec — "deferred (no current spec home)" is the honest current state. No test pins the prior string (`grep` for the old wording across `tests/` and `examples/` returned zero matches).
  - **`_validate_meta` docstring (refactor-induced spot-check):** already updated during the logic pass at `types/base.py:513-539` — the docstring's Returns section names the `_ValidatedMeta` snapshot and its five fields (`interfaces`, `primary`, `optimizer_hints`, `fields_spec`, `exclude_spec`) and calls out the single-pass-through-`__init_subclass__` contract. No further edit needed.
  - **`_validate_optimizer_hints` docstring (refactor-induced spot-check):** already updated during the logic pass at `types/base.py:580-603` — the Args section describes the new `(hints, fields)` signature, calls out that `hints` is pre-normalized by `_meta_optimizer_hints` inside `_validate_meta`, and notes the model is derived from `fields[0].model`. No further edit needed.
  - **`_ValidatedMeta` docstring (refactor-induced spot-check):** already added during the logic pass at `types/base.py:498-505` — explains the thread-through purpose and the shape-gate-once contract. No further edit needed.

### Carry-forward dispositions

- **M3 deferred to follow-up review cycle (post-0.0.6).** The `_collect_consumer_authored_fields(cls, fields) -> tuple[frozenset[str], dict[str, frozenset[str]]]` extraction (would own `types/base.py:170-187`) and the `_assert_no_relay_id_collision(cls, relay_shaped)` extraction (would own `types/base.py:189-213`) are substantial refactors of `__init_subclass__`'s high-branch-count top-level body. Worker 1's artifact framed M3 as "Defer until the `primary` thread-through above lands so the two refactors compose" — the thread-through landed this cycle, so the next review cycle on `types/base.py` is the right home. Recording the carry-forward here so the project pass can track it.
- **L4 revert documented; pinning test recorded.** During the logic pass, Worker 2 attempted to move the `cls._is_default_get_queryset = not has_custom_get_queryset` stamp AFTER the `meta is None` early-return and the finalized-registry raise (the artifact's recommendation). The existing test `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_abstract_base_without_meta` (lines 556-589 with the docstring at 557-568 explicitly labelling the deferred-stamp shape a former P1 bug) requires the stamp to happen BEFORE the `meta is None` early-return so an abstract base that overrides `get_queryset` without declaring Meta still flips the flag for concrete subclasses inheriting from it. The artifact's "Practical impact is nil" justification missed this consumer-supported abstract-base pattern. Reverted, with an anchor comment at `types/base.py:148-153` naming the invariant and the pinning test.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).
- No pytest run per cycle instructions.

---

## Changelog disposition

### Warranted?

**Not warranted.**

### Reason

All cycle changes are internal refactors with no public API change, no behavior change, and no test-surface change:

- `_validate_meta` now returns a `_ValidatedMeta` NamedTuple bundling `interfaces`, `primary`, `optimizer_hints`, `fields_spec`, `exclude_spec`. `_ValidatedMeta` is private (leading underscore); the return value is consumed only by `__init_subclass__`. Internal refactor.
- `_validate_optimizer_hints` signature changed from `(meta, fields)` to `(hints: dict[str, Any], fields)`. The function was already private (leading underscore) and has no consumer call sites. Internal refactor.
- L1 (`cls.__annotations__` direct access in place of defensive `getattr`): syntactic cleanup; identical behavior on Python ≥3.10 (pyproject pins `>=3.10,<4.0`). Internal.
- L2 (`_record_pending_relation` deleted; inlined at `_build_annotations`): private helper removed; no consumer surface affected. Internal.
- L5 (docstring + error-message version stamps in `_validate_interfaces`): the constraint wording ("Lazy/forward-reference interface lookup is …") is preserved; only the trailing version stamp changed ("for 0.0.5" → "deferred (no current spec home)"). No test pins the prior string. The error message is technically consumer-visible at raise time, but the constraint is unchanged and the new wording is more durable. Substring-compatible additive cleanup, not a contract change.

Matches worker-memory's "Not warranted" pattern for internal-only changes / docstring polish / DRY-consolidations that return identical outputs. `AGENTS.md`'s "Do not update CHANGELOG.md unless explicitly instructed" plus the active review plan's silence on this cycle = no edit.

### What was done

No `CHANGELOG.md` edit. Disposition recorded here in the artifact per the standing workflow.

### Validation

- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

---

## Iteration log

_appended by Worker 2 / Worker 3 on each re-pass._

## Verification (Worker 3, pass 2)

### Comment verification outcome

L5 wording is version-neutral and preserves the constraint: at `types/base.py:441-444`, "Slice 4's Phase 2.5" replaced with "``finalize_django_types()`` (Relay finalization phase)"; at `types/base.py:465-466`, "out of scope for 0.0.5" replaced with "deferred (no current spec home)". The constraint phrasing ("Lazy/forward-reference interface lookup is …") is preserved verbatim; only the version anchor / spec stamp changed. Refactor-induced docstring updates accurately describe the new shapes:

- `_ValidatedMeta` docstring at `types/base.py:498-505` explains the thread-through purpose and shape-gate-once contract.
- `_validate_meta` Returns section at `types/base.py:530-536` names the `_ValidatedMeta` snapshot and its five fields (`interfaces`, `primary`, `optimizer_hints`, `fields_spec`, `exclude_spec`) and calls out the single-pass thread-through contract.
- `_validate_optimizer_hints` Args section at `types/base.py:597-603` describes the new `(hints, fields)` signature, notes `hints` is pre-normalized by `_meta_optimizer_hints` inside `_validate_meta`, and explains the model is derived from `fields[0].model`.

M3 deferral and L4 revert correctly recorded in the artifact's Comment pass / Carry-forward dispositions block.

### Changelog verification outcome

Not warranted accepted — `_ValidatedMeta` is private (leading underscore), `_validate_meta`'s new return is internal-only (consumed only by `__init_subclass__`), `_validate_optimizer_hints`'s new signature is private, L1/L2 are syntactic cleanup with no consumer surface, and L5's wording change preserves the constraint. All refactors are internal; no public API change. Disposition cites both the `AGENTS.md` changelog ban and the active plan's silence on this cycle. `git diff -- CHANGELOG.md` returns empty. Accepted.

### Verification outcome

`cycle accepted; verified`.
