# Review — spec-029 implementation (commit `2d1f296` "Finish spec-029-consumer_dx_cleanup-0_0_9.md")

**Verdict: APPROVE / ship-ready.** All three functional slices are implemented, and the
implementation is unusually faithful to the spec — every Decision (3–11) is honored, the test
plan is covered in full (and over-covered in two places), `ruff check` / `ruff format --check`
are clean, and every spec-029-touched test passes. There is **one thing to be aware of** (a
batch of pre-existing, unrelated `kanban` failures in the full suite) and a couple of
**low-severity polish notes**. None block the card.

## How this was reviewed

- Read the full spec (`docs/spec-029-consumer_dx_cleanup-0_0_9.md`, all 825 lines) and diffed the
  commit against it, Decision by Decision.
- Read the four source diffs in full: `types/converters.py`, `types/base.py`,
  `management/commands/inspect_django_type.py` (new), `optimizer/extension.py`.
- Verified the introspection command's assumptions against the live codebase (`field_map`
  keying = `snake_case(f.name)`; `FieldMeta.relation_kind` / `is_many_side` / `nullable`;
  `DjangoTypeDefinition.origin/model/selected_fields/field_map/interfaces`; the relation
  annotation key written by the finalizer = `pending.field_name`).
- Ran the **Slice 1 forbidden-form gate** (DoD item 4), the **glossary checker** (DoD item 1),
  `ruff`, and the touched test suites — package + example.

## What I verified green

| Check | Result |
| --- | --- |
| `ruff check` (pkg + examples + tests) | `All checks passed!` |
| `ruff format --check` | `219 files already formatted` |
| `check_spec_glossary.py --spec …029…` | `OK: 44 terms` (41 + the 3 net-new symbols now anchored) |
| Forbidden-form grep (`[…()]`, bare class, `[ext]`, `[_CaptureExt()]`, `lambda: …()`) | **0 hits** in active source/docs |
| All `extensions=[…]` sites singleton-factory | yes (68 sites; the only non-`lambda` hits are `[...]` prose placeholders in 3 docstrings) |
| Touched package suites (converters, base, inspect failure-modes, extension, relay-id, field-meta, list-field, generic-fk) | **283 passed, 2 skipped** |
| Example inspect suite + the two live-HTTP override acceptance tests | **10 passed** |
| Version files (`pyproject.toml` / `__version__` / `test_init.py` / `uv.lock`) | **untouched** (Decision 11 ✓) |
| CHANGELOG bullets | under `[Unreleased]`, no `0.0.9` heading promoted (Decision 11 ✓) |

## Slice-by-slice

### Slice 1 — `extensions=` singleton-factory migration — ✓ complete
- Every instance/named/bare-class/`_CaptureExt()` site is now `extensions=[lambda: <instance>]`,
  function-local where a test asserts on `cache_info()` and module-level where there is one schema
  per module — exactly the per-construction-site granularity Decision 3 (rev4) demands.
- `examples/fakeshop/config/schema.py` migrated off the bare-class **cold-cache regression** to the
  singleton factory; `GOAL.md` gained `DjangoOptimizerExtension` via the factory (it previously
  passed no `extensions=` at all); `optimizer/extension.py`'s docstring now teaches the factory form.
- The no-warning regression test landed:
  `tests/optimizer/test_extension.py::test_singleton_factory_extensions_form_emits_no_deprecation_warning`,
  and `test_scalars.py`'s `-W error::DeprecationWarning` subprocess still passes — so the migration
  genuinely removed the warning rather than masking it.

### Slice 2 — `inspect_django_type` — ✓ complete
- Command shape matches Decision 4 precisely: dot-dispatch resolution (`import_string` for dotted,
  re-raising the **original** import error as `CommandError`; unique-`__name__` registry lookup for
  bare names with a candidate-listing ambiguity branch), `--schema` via
  `import_module_symbol(…, default_symbol_name="schema")`, the resolved-annotation read from
  `origin.__annotations__` (not a `convert_scalar` re-run), and the Relay-suppressed-pk special case
  sourcing `GlobalID!` from the interface instead of `KeyError`-ing on `origin.__annotations__[pk]`.
- Both no-definition and `finalized is False` are distinct error branches (handle() lines 88–95).
- **The cold-path test does it right**: `test_inspect_with_schema_option` evicts `_SCHEMA_MODULES`
  from `sys.modules` *and* clears the registry before `call_command` — i.e. it does not rely on the
  `registry.clear()`-alone non-cold-start the spec explicitly warned against — and parametrizes both
  `config.schema` and `config.schema:schema` selector forms.
- All five failure-mode tests from the test plan are present and pass.

### Slice 3 — `Meta.nullable_overrides` / `Meta.required_overrides` — ✓ complete
- `convert_scalar` grows the keyword-only `force_nullable: bool | None` tri-state; `effective_null`
  is computed once and read at every widening site (Array / HStore / choice / scalar). The
  `ArrayField` recursion is correctly left `force_nullable`-unset so only the *outer* nullability is
  overridden — matches Decision 7 and the edge-case spec. `converters.py` shows **100% coverage**.
- Validation is staged exactly per Decision 8: shape + normalize + both-sets collision in
  `_validate_meta`; `_validate_nullability_override_targets` in `__init_subclass__` (after
  `_select_fields` + `consumer_authored_fields` + the Relay-shape check), deriving **two distinct
  name sets** (model-wide for *unknown* via `_format_unknown_fields_error`; selected for *excluded*)
  as separate error paths so the `Meta.exclude` contract isn't collapsed into "unknown".
- Test coverage **exceeds** the plan: beyond the prescribed cases, it adds
  `test_override_relay_suppressed_pk_raises` and `test_override_non_sequence_raises` — both genuine
  paths worth pinning.
- The live acceptance type is wired correctly: `BookType` marked `primary = True`,
  `NullabilityOverrideBookType` (`primary = False`) flips `title` → `String` and `subtitle` →
  `String!`, and its root resolver returns `.exclude(subtitle__isnull=True).order_by("id")` so the
  forced-non-null contract holds at the boundary with deterministic ordering. The SDL-flip test and
  the queryable-API test both pass; the existing `BookType` / `scalars` baselines are undisturbed.

## ⚠️ One thing to flag (not caused by this commit)

**The full suite is red — 32 failures — but every one is in the `kanban` example app, unrelated to
spec-029.** Root cause: `examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_glossary_link`
(added by the separate commit `a4303b7 "glossary: require done card term links"`) now raises
`ValidationError: Done kanban cards require at least one glossary link.` The kanban test fixtures
(`_seed_board`) seed DONE cards without glossary links and trip it.

Evidence it is **not** a spec-029 regression:
- No `kanban` file is in commit `2d1f296` (`git show --stat HEAD | grep kanban` → empty).
- Every other live-HTTP suite (`library`, `products`, `scalars`, `glossary`) passes — so the shared
  `config/schema.py` singleton-factory change is exonerated.
- The traceback is in a kanban pre-save signal / fixture mismatch, not in any spec-029 code path.

Action: none for this card, but the maintainer should know `uv run pytest` is currently red on
`main` from the kanban/glossary work, which means the **100% coverage gate (DoD item 17) can't be
confirmed green by CI until the kanban fixtures are reconciled with that new signal.** Recommend a
separate fix (seed the kanban DONE-card fixtures with a glossary link, or scope the signal). This is
the kind of cross-agent collision the spec already anticipated in its KANBAN-regeneration note.

## Low-severity polish (optional — no change required to ship)

- **P3 — converter label names the concrete field class, not the matched `SCALAR_MAP` key.**
  `_scalar_row` prints `SCALAR_MAP[{type(field).__name__}]` (inspect cmd line 201). For a consumer
  subclass of a supported field (resolved via the MRO walk), this prints e.g.
  `SCALAR_MAP[MyCustomTextField]` when the row that actually fired is `TextField`. For every field in
  the fakeshop suite the two coincide, so it's invisible today; if you want the label to be literally
  "which row fired," it would need the matched MRO ancestor rather than `type(field).__name__`. Spec
  §Decision 4 calls the exact layout an implementation detail, so this is purely a precision nit.
- **P3 — `scalar_for_field(field)` in `_scalar_row` is effectively dead-defensive.** It's called only
  for its raise-on-unsupported side effect (line 200), but by the time you're inspecting a *finalized*
  type, every scalar field already survived `convert_scalar` at construction — so it can't fire.
  Harmless, and the comment is honest about the intent; leaving it is fine.
- **P3 — relation converter text differs from the illustrative output.** The command prints
  `relation: {field_meta.relation_kind}` (e.g. `relation: many_to_many`), whereas the spec's
  illustrative table showed `relation: M2M` / `forward FK` / `reverse FK`. Spec-permitted (layout is
  an impl detail) and the tests assert on the GraphQL-type column, so this is just a note in case you
  prefer the friendlier labels.

## Remaining wrap items (expected, per the spec — not defects)
- The **card-completion wrap** (move `WIP-ALPHA-029-0.0.9` → `DONE-NNN-0.0.9` in `KANBAN.md`) and the
  **joint `0.0.9` version cut** are intentionally deferred (spec Status line + Decision 11). `KANBAN.md`
  is not in this commit, which is correct for "three functional slices done, Slice 4 pending."
- Slice 3's *optional* `README.md` / `TODAY.md` capability-list mention was not added — the spec
  marked it optional ("include only if the surface is reflected there"), so this is a non-issue.

---
*Reviewed against spec rev 8. Full suite: 1355 passed, 3 skipped, 32 failed (all kanban-app,
unrelated). Spec-029 scope: 100% green.*
