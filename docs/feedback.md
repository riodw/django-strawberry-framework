# Bug-hunt review — `django_strawberry_framework/` staged changes

Reviewed against staged diff (`git diff --staged django_strawberry_framework/`) and
`docs/bug_hunt/bug_hunt.57ce0bf.md` per-file result notes.

Files reviewed: `optimizer/walker.py`, `registry.py`, `types/base.py`,
`types/converters.py`, `utils/typing.py`.

Each finding cites the bug-hunt result notes; verification artefacts (scratch
`test_*.py` repros and one ad-hoc pytest run) are noted inline.

## Verified valid fixes

### `optimizer/walker.py` — `OptimizerHint` error messages now name the type
`_apply_hint` and `_prefetch_hint_for_path` previously raised `ConfigurationError`
messages that mentioned only the Django field name (`'items'`); the staged
change threads `type_cls.__name__` through so messages now read
`OptimizerHint.select_related() on CategoryType.items: …`. Matches the dicta
"can a consumer grep the error message back to the specific model / field /
site that caused it?" rule and aligns the wording with the spec-014 H1 audit
style. **Confirmed valid.**

### `registry.py` — duplicate-primary error now names the model
The pre-existing message (`"X is already declared primary as Y"`) omitted the
model name. The new message includes it: `"Cannot register X as primary for
Model; Y is already the primary type"`. Matches the same triage-by-grep rule.
**Confirmed valid.**

### `types/base.py` — three fixes, all valid
1. `_validate_optimizer_hints` now receives `model` explicitly instead of
   inferring it via `fields[0].model`. The old shape would raise `IndexError`
   on an empty `fields` tuple (e.g. a `Meta.exclude` covering every field with
   `optimizer_hints` set). The replacement is also clearer at the call site —
   `meta.model` is the authoritative source. **Confirmed valid.**
2. `Meta.fields` / `Meta.exclude` mutual-exclusivity check switched from
   `meta.__dict__` membership to `getattr(meta, ..., None) is not None`, so it
   now also fires when `fields` or `exclude` is inherited from a parent
   `class BaseMeta`. Verified with `test_inherited_meta.py`: both the
   declared-on-child case and the inherited-from-`BaseMeta` case now raise
   `Meta.fields and Meta.exclude are mutually exclusive`. **Confirmed valid.**
3. Shadow error in `_consumer_assigned_fields` now reports
   `f"{cls.__name__}.{field.name} shadows …"` instead of `field.model.__name__`.
   The error is about a class-attribute on the `DjangoType` subclass, not the
   underlying Django model, so the `cls.__name__` attribution is the correct
   one. **Confirmed valid.**

### `types/converters.py` — `DurationField` / `BinaryField` removed from `SCALAR_MAP`
Verified directly that Strawberry refuses both types at schema construction
time:

```
$ uv run python test_strawberry_timedelta.py
Schema creation failed: TypeError Query fields cannot be resolved.
  Unexpected type '<class 'datetime.timedelta'>'
$ uv run python test_strawberry_bytes.py
bytes Schema creation failed: TypeError Query fields cannot be resolved.
  Unexpected type '<class 'bytes'>'
```

With the staged change `convert_scalar` raises `ConfigurationError(
"Unsupported Django field type …")` at class-definition time instead of
letting Strawberry's downstream `TypeError` fire later from a less-localized
frame. **Confirmed valid.**

### `utils/typing.py` — `unwrap_return_type` handles bare `list` / `typing.List`
Verified with `test_typing_verify.py`:

```
unwrap_return_type(typing.List): typing.Any   # was IndexError before
unwrap_return_type(list):        typing.Any   # was 'list' (un-peeled) before
unwrap_return_type(list[int]):   <class 'int'>
unwrap_return_type(int):         <class 'int'>
```

The pre-existing `get_args(rt)[0]` branch crashed when `rt is typing.List`
(bare, no parameters) because `get_origin(typing.List) is list` but
`get_args(typing.List)` returns `()`. The new code returns `typing.Any` for
both bare forms, which is the correct "unknown element type" sentinel.
**Confirmed valid.**

## Issues introduced by the bug-hunt fixes

### High — 5 existing tests now fail because the fixes did not update their pins
AGENTS.md mandates "Add tests in the same change as code; sweep all three
test trees for orphan imports when removing code". The dicta itself echoes
that under "For every High-priority bug suspected: is there a test that
pins the corrected behavior?". The fixes shipped without updating tests
that already pinned the old error wording / function signature, so the
package test suite is now red:

1. `tests/test_registry.py::test_register_two_primaries_for_same_model_raises_configuration_error`
   (test file line 761) — regex `"already declared primary as ItemType"`
   no longer matches the new message
   `"Cannot register AdminItemType as primary for Item; ItemType is already
   the primary type"`. Fix: replace the pin with something like
   `match="ItemType is already the primary type"` (or `"Cannot register .* as
   primary for Item"`) — needs to be grep-stable post-rename.

2. `tests/optimizer/test_walker.py::test_plan_force_select_hint_raises_for_many_side_relation`
   (test file line 1208) — regex `r"OptimizerHint\.select_related.*'items'"`
   expected single-quoted `'items'`; new message is
   `OptimizerHint.select_related() on CategoryType.items: …` (unquoted,
   dotted). Fix: switch the pin to
   `r"OptimizerHint\.select_related\(\) on CategoryType\.items"` or similar.

3. `tests/optimizer/test_walker.py::test_prefetch_hint_for_path_rejects_prefetch_without_lookup`
   (test file lines 1483-1491) — calls `_prefetch_hint_for_path(no_lookup,
   django_name=..., full_path=...)`. The function now requires `type_name`
   as a keyword-only argument; the test raises
   `TypeError: _prefetch_hint_for_path() missing 1 required keyword-only
   argument: 'type_name'`. Fix: pass a dummy `type_name="ItemType"` (or
   similar) in this test and the next two.

4. `tests/optimizer/test_walker.py::test_prefetch_hint_for_path_adapts_nested_lookup_under_parent`
   (test file lines 1505-1509) — same `TypeError` for the missing
   `type_name`.

5. `tests/optimizer/test_walker.py::test_prefetch_hint_for_path_rejects_mismatched_lookup`
   (test file lines 1532-1536) — same `TypeError` for the missing
   `type_name`.

Verification: `uv run pytest …test_prefetch_hint_for_path_rejects_prefetch_without_lookup
…test_prefetch_hint_for_path_adapts_nested_lookup_under_parent
…test_prefetch_hint_for_path_rejects_mismatched_lookup
…test_plan_force_select_hint_raises_for_many_side_relation` reports four
failures; `uv run pytest …test_register_two_primaries_for_same_model_raises_configuration_error`
reports the fifth.

Also worth adding (the dicta calls these "untested territory"):
  - A positive test that the new error messages **include** the type name
    (e.g. `match="CategoryType\\.items"` on the `select_related` raise),
    so a future cosmetics-only refactor of the message can't silently drop
    the type name again.
  - A test that `_validate_optimizer_hints` does not `IndexError` when
    `fields` is empty (the empty-`fields` shape is the bug the new
    `model` parameter defends against).
  - A test that `Meta.fields` inherited from a parent `Meta` raises when
    the child declares `exclude` — the inheritance branch is the actual
    new behavior introduced by the `getattr(…, None) is not None` switch.
  - A test that `DurationField` / `BinaryField` on `Meta.fields = "__all__"`
    raise `Unsupported Django field type` (or at least one of them) so
    the regression cannot creep back via someone re-adding the entry.

### Medium — stale docstring on `_validate_optimizer_hints`
In `types/base.py:600-606` the `Args` block still reads:

```
fields: The Meta-filtered list of Django field objects produced
    by ``_select_fields``. Used to derive the model and the
    selected relation field names.
```

The `model` is no longer derived from `fields`; the new `model` keyword
parameter is not documented at all. Recommend:
  - Drop the "Used to derive the model" clause from the `fields` doc.
  - Add a new `model:` entry: `"The Django model whose ``_meta.get_fields()``
    defines the valid hint key surface. Threaded from ``meta.model`` so the
    empty-``fields`` shape is no longer fatal."`

Dicta category: "Refactor leftovers — Did a refactor change a signature or
return shape but leave the docstring describing the old contract?".

### Medium — `"UnknownType"` fallback in `walker.py` is unreachable in practice
The staged change adds `type_name = type_cls.__name__ if type_cls is not
None else "UnknownType"` at three sites in `_apply_hint` /
`_prefetch_hint_for_path` (walker.py lines 435, 449, and indirectly via
the 509/520 paths once the helper is reached from `_apply_hint`).

Tracing the call graph in `_walk_selections` (walker.py:241-256):

```python
hints_map = _resolve_optimizer_hints(type_cls)
hint = hints_map.get(django_name)
if hint is not None and _apply_hint(...):
```

`_resolve_optimizer_hints(None)` returns `{}` (walker.py:121-122), so when
`type_cls is None` the `hints_map` is empty, `hint` is always `None`, and
`_apply_hint` is never entered. The `"UnknownType"` literal is therefore
dead under the production code path. Two options:
  - Drop the fallback (replace with plain `type_cls.__name__`) and let
    `AttributeError` fire if a future caller invokes `_apply_hint`
    directly — the dicta prefers "fails loud" over silent defaults.
  - Keep the fallback **and** add a direct-call test that pins the
    `"UnknownType.<name>"` shape; otherwise the literal will rot.

Dicta category: "Where a default value is 'obviously unreachable' — try
to reach it. Defaults marked dead are often load-bearing under one input
shape." In this case the default is genuinely unreachable, so it should
either be deleted or covered by a test that proves a reachable input.

### Medium — `converters.py` removal is a public-API change without a pin
The bug-hunt note for `types/converters.py` claims `tests/types/test_converters.py
passed`. Running it confirms 54 tests pass, but **none of those tests
exercise `DurationField` or `BinaryField`** — grep on the test file is
empty for both names. The new fail-fast `ConfigurationError` is therefore
unpinned. A consumer using `Meta.fields = "__all__"` on a model with
either field type will hit the new error at class-definition time rather
than at schema build, which is a behaviour change worth a regression test
(see the High-severity "untested territory" suggestion above).

A secondary concern: the docstring on `SCALAR_MAP` (converters.py:22-27)
advertises `SCALAR_MAP[FieldCls] = py_type` as the extension hook. For
`BinaryField` a consumer can plug in `strawberry.scalars.Base64`; for
`DurationField` there is no first-party Strawberry scalar at all — the
consumer has to define a custom scalar themselves. A short inline note
near the removed entries (or near the unsupported-type raise in
`convert_scalar`) pointing consumers at the SCALAR_MAP hook and at
`strawberry.scalars.Base64` would soften the breakage.

### Low — subtle behaviour shift in `fields`/`exclude` exclusivity check
The old check (`"fields" in declared and "exclude" in declared` over
`meta.__dict__`) counted any literal class-body assignment, including
`fields = None`. The new check (`getattr(meta, "fields", None) is not None`)
treats an explicit `fields = None` as "unset". The new semantics are
arguably more intuitive (`None` ≡ "not specified"), and they match the
`_normalize_fields_spec` rule that returns `None` for `None`. Worth a
one-line code comment near the new `has_fields` / `has_exclude` block
explaining the inheritance intent so a future maintainer doesn't "fix"
it back to `__dict__`-membership.

## Net assessment
All five findings the bug hunt surfaced were valid bugs, and the patches
are directionally correct. The blocker for landing the staged diff is the
five broken tests; secondary cleanups (stale docstring, dead
`"UnknownType"` fallback, missing positive pins) can land in the same
change or as immediate follow-ups.