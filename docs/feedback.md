# Feedback — `spec-029-consumer_dx_cleanup-0_0_9.md` (review of Revision 2)

Reviewed 2026-06-04 against the repo at HEAD. Findings are verified against the actual
source, the **locked** Strawberry version, and the example project — not taken from the
spec's own assertions. Priority convention matches the spec's: **P1** = foundational
(changes the design or a load-bearing claim), **P2** = correctness/completeness gap to
close before or early in implementation, **P3** = accuracy/polish.

**Verdict:** strong, unusually well-researched spec. The internal-source claims are almost
all exactly right (see [Verified correct](#verified-correct) — I re-checked ~30 of them).
The real problems are concentrated in **one place**: the Strawberry extension-lifecycle
model underpinning Decision 3 / Slice 1 describes a Strawberry that the repo **no longer
locks**. The *conclusion* (keep the instance form) survives — arguably strengthens — but
the *mechanism*, and two specific downstream claims, are false for the locked version, and
the spec misses the form that actually resolves the conflict it calls irreconcilable.

---

## P1 — foundational

### P1.1 — The Strawberry extension-lifecycle model is stale for the locked version

Decision 3, Current state (line 114), Problem statement (line 97), Borrowing posture
(line 141), and Risks (line 569) all rest on this model, inherited from spec-004:

> Strawberry instantiates `_sync_extensions` once (a `@cached_property` …) but
> `_async_extensions` is a plain `@property` that yields a fresh instance per access.
> (spec-029 line 272)

**This is not how the locked Strawberry behaves.** The repo pins `strawberry-graphql>=0.262.0`
(`pyproject.toml:30`) and locks/installs **0.316.0** (`uv.lock:439-440`). In 0.316.0 the
`_sync_extensions` / `_async_extensions` split **no longer exists** — it was refactored into a
single per-request accessor:

```python
# .venv/.../strawberry/schema/schema.py:388
def get_extensions(self, sync: bool = False) -> list[SchemaExtension]:
    resolved: list[SchemaExtension] = [
        ext if isinstance(ext, SchemaExtension) else ext()   # line 393
        for ext in self.extensions
    ]
```

`execute()` and `execute_sync()` both call this **per request**. Consequences for the spec:

- A **bare class** or **constructing factory** gets a fresh instance **on every request, in
  both sync *and* async** — not "async only." So the spec's repeated claim that the class form
  is "harmless for the sync-only fakeshop tests because `_sync_extensions` is a `@cached_property`,
  so the bare class yields one shared instance in sync mode" (lines 70, 294, 570) is **false**
  for 0.316.0: the fakeshop class-form drift in `config/schema.py:36` and `TODAY.md` gets a cold
  cache every request even in sync. (The *test-correctness* conclusion — "leave them alone" — may
  still hold, since a cold cache changes performance, not results; but the stated reason is wrong.)
- The spec treats Strawberry's behavior as fixed when it **varies across the package's own
  supported range** (`>=0.262.0`, open-ended). The `_sync`/`_async` model was accurate when
  spec-004's spike ran (2026-04-30); the locked dep has since moved. Decision 3 is therefore a
  version-dependent argument presented as version-independent.

**Recommended fix:** re-derive Decision 3 from 0.316.0's actual `get_extensions` behavior and
pin the claims to a version. Note that the conclusion *improves* under 0.316.0: the instance
form is now the **only** form that gets any plan-cache hits in **either** mode (a fresh
instance per request means zero hits for class/factory in sync too), so "keep the instance"
is more strongly motivated, not less. The glossary `Plan cache` / `Strictness mode` entries the
spec cites likely carry the same stale model — flag them for re-verification (out of scope to
fix here, but they feed this spec).

### P1.2 — "There is no `DeprecationWarning` to chase" is false for 0.316.0

Slice 1 test plan (line 501) and DoD item 4 (line 598) both assert:

> There is no `DeprecationWarning` to chase: Strawberry accepts a passed-in instance via the
> `isinstance` passthrough in `get_extensions()` and does not warn on it.

Strawberry 0.316.0 **does** warn — at `Schema.__init__`, separately from the `get_extensions`
passthrough:

```python
# .venv/.../strawberry/schema/schema.py:270-282
if any(isinstance(ext, SchemaExtension) for ext in self.extensions):
    warnings.warn(
        "Passing an extension instance to `extensions=[...]` is "
        "deprecated and will be removed in a future release. "
        "Pass the class itself, or a factory callable …",
        DeprecationWarning, stacklevel=2,
    )
```

So under Decision 3, **every schema constructed with the instance form emits a live
`DeprecationWarning`** that says the form "will be removed in a future release." Impact:

- **Not test-breaking today.** `pytest.ini` has no `filterwarnings = error`, and CI just runs
  `uv run pytest` (`.github/workflows/django.yml:97`), so the ~19 existing instance-form sites
  (`tests/optimizer/test_extension.py:207,254,306,…`) pass despite the warning.
- **But the project demonstrably cares about deprecation hygiene** — `tests/test_scalars.py:256`
  spins up a subprocess under `-W error::DeprecationWarning` precisely to guard against one.
  Decision 3 should not claim the warning is absent; it should *decide what to do about it*:
  accept it, suppress it locally (`warnings.filterwarnings("ignore", ...)` at the documented
  snippet / in a fixture), or resolve it (see P1.3). Right now the spec asserts the opposite of
  reality and so never makes that decision.

### P1.3 — "No modernize-without-regression form exists" is false — the singleton-factory resolves it

Decision 3 frames the conflict as irreconcilable:

> No "modernize without regression" form exists while the cache is instance-bound (the `lambda`
> factory has the same fresh-per-async-access problem) … (line 287; also line 294)

That is true only for a **constructing** factory (`lambda: DjangoOptimizerExtension()`). It is
**not** true for a factory that closes over a **module-level singleton**:

```python
_OPTIMIZER = DjangoOptimizerExtension()           # one instance, one plan cache
schema = strawberry.Schema(query=Query, extensions=[lambda: _OPTIMIZER])
```

Under 0.316.0 this form:
- **emits no DeprecationWarning** — the `extensions` tuple contains a *callable*, not a
  `SchemaExtension` instance, so the `any(isinstance(...))` check at `schema.py:270` is `False`;
- **preserves the plan cache** — `get_extensions` runs `ext()` and gets the *same* `_OPTIMIZER`
  back every request (`schema.py:393`), in both sync and async.

Its caching and concurrency semantics are **identical** to the bare-instance form the spec keeps
(one shared instance across all requests) — it just packages that instance as a callable to dodge
the deprecation. So there *is* a modernize-without-regression form, and under 0.316.0 it is
**strictly better** than the bare instance (same behavior, no warning), without relocating the
plan cache. The Strawberry warning message itself points at "a factory callable" as the fix.

**Recommended fix:** add this as a considered option in Decision 3 and either adopt it (it
directly closes P1.2) or reject it with a concrete reason. One caveat to verify before adopting:
that the extension holds no *per-request* mutable state on `self` that sharing would corrupt —
but the kept instance form already shares one instance across all concurrent requests, so the
sharing semantics are unchanged (and `extension.py`'s per-request state is already on `ContextVar`s,
not `self`, per `on_execute`). If that holds, "keep the bare instance and document why" is no
longer the honest move; "wrap the singleton in a factory" is.

---

## P2 — correctness / completeness gaps

### P2.1 — Decision 4's output contract doesn't cover the Relay-suppressed pk

The contract is "read resolved GraphQL type + nullability from `origin.__annotations__`"
(line 305). But the Relay-suppressed pk **`continue`s past `convert_scalar`** and is therefore
**never written to `cls.__annotations__`**:

```python
# django_strawberry_framework/types/base.py:947-957
if suppress_pk_annotation and field.name == pk_name:
    continue                       # no annotation synthesized for the pk
annotations[field.name] = convert_scalar(field, cls.__name__)
```

The pk *does* stay in `selected_fields` / `field_map`. So a command that iterates
`selected_fields` and does `origin.__annotations__[field.name]` will **`KeyError` on the pk** of
any Relay-shaped type — the exact row the spec's example renders as `id → GlobalID!`. The
`GlobalID!` type comes from the `relay.Node` interface, not the type's own annotations, and the
contract never says how to source it. **Fix:** specify the suppressed-pk branch in Decision 4
(source it from the interface / hardcode `GlobalID!` when `suppress_pk_annotation`), and add a
test for "inspect a Relay-shaped type's pk row."

### P2.2 — The illustrative output (lines 191-200) is wrong: `BookType` is not Relay-shaped

The example shows `id → BigAutoField → GlobalID! → relay.Node id` for **BookType**. But BookType's
`Meta` (`apps/library/schema.py:58-70`) declares **no `interfaces`** — only **GenreType** is
Relay-Node (`schema.py:119`; confirmed by `test_library_api.py:834`). A non-Relay BookType's `id`
is **not** suppressed and **not** `GlobalID!`; `convert_scalar` renders it as a plain scalar.
**Fix:** either move the `GlobalID!` row to a genuinely Relay-shaped type (GenreType), or show
BookType's actual non-Relay pk type. This also affects `test_inspect_relation_field_rows`
(line 509) — its `shelf`/`genres`/`loans` assertions are fine, but any pk assertion on BookType
must not expect `GlobalID!`.

### P2.3 — `inspect_django_type` likely errors out on a cold CLI invocation — nothing triggers finalization

As specified, `handle` resolves a type and reads its definition but never imports the project
schema or calls `finalize_django_types()`. Trace a real shell invocation:

- `manage.py inspect_django_type BookType` (bare name): in a cold process nothing has imported
  `apps.library.schema`, so BookType isn't registered → registry lookup finds zero → "unresolvable"
  `CommandError`.
- `manage.py inspect_django_type apps.library.schema.BookType` (dotted): `import_string` imports the
  module → BookType registers in `__init_subclass__`, but `finalize_django_types()` has **not** run
  → `definition.finalized is False` → "finalize first" `CommandError`.

So the command's primary use case fails from the shell. The happy-path tests only pass because
pytest imports `config.schema` (which finalizes) first. Contrast `export_schema`, which takes a
**schema** argument and imports it — self-triggering finalize + construction. The "import the
project schema first" message (line 309) isn't actionable from a plain CLI. **Fix:** decide how
the command reaches a finalized state on its own — e.g. a `--schema`/configured-schema import like
`export_schema`, or call `finalize_django_types()` after resolution (note finalize needs *all*
types registered, so importing only the target module isn't enough). This is a real diagnostic-value
gap, not just an error-message wording issue.

### P2.4 — A second `DjangoType` on `Book` may perturb schema-wide assertions the spec assumes are untouched

Slice 3 adds `NullabilityOverrideBookType`, exposes it via a root field (so it enters the SDL),
and flips `BookType` to `Meta.primary = True`. The spec asserts the existing `BookType` and
`scalars` assertions are "untouched" (lines 84, 116, 537), and the per-field reasoning checks out
(relation targets still resolve to the now-primary BookType — line 490). **But** today Book has
exactly one registered type, and the spec never checks for a test that asserts the **total
registered-type count** or snapshots the **full SDL / type list** — a new reachable type would
change either. **Fix:** add a verification step confirming no such schema-wide/count assertion
exists (grep `test_query/` and any schema-snapshot test) before declaring the existing suite
undisturbed. Cheap to confirm; expensive to discover mid-implementation.

---

## P3 — accuracy / polish

### P3.1 — "NEXT.md … forbids creating glossary entries" overstates the rule

Line 561 says the NEXT.md flow "forbids creating glossary entries" during authoring. NEXT.md
Step 7 actually **defers** glossary anchoring to the companion CSV; it doesn't forbid authoring an
entry. The spec's *handling* is correct and well-reasoned (entries land in Slice 2/3 doc steps;
the three net-new symbols are omitted from the CSV so `check_spec_glossary.py` stays green — all
verified true). Only the characterization is slightly off. **Fix:** soften to "defers glossary
anchoring until the heading ships" or cite the exact Step-7 provision.

---

## Verified correct (re-checked, no action needed)

So the above findings aren't mistaken for the whole picture — these spec claims were checked
against source and hold exactly:

- **Meta-key sets** — `ALLOWED_META_KEYS` and `DEFERRED_META_KEYS` match the spec verbatim
  (`base.py:48-65`); neither override key exists today; the unknown-key guard is at `base.py:669`.
- **Three-stage validation ordering** — `_validate_meta` runs at `base.py:229`, *before*
  `_select_fields` (230), `consumer_authored_fields` (256-263), and the Relay check (264). This is
  exactly why Rev2's P1 reshaping of Decision 8 (single helper → three stages) was necessary and
  correct. `_validate_filterset_class`/`_validate_orderset_class` use the in-function-import,
  raise-ConfigurationError shape the spec cites as the template (`base.py:68-119`).
- **`convert_scalar`** — signature is `(field, type_name)` with no override param (`converters.py:142`);
  final widening is `if field.null: py_type = py_type | None` (232-234); ArrayField/HStoreField
  early-return and each widen independently (197-224); **choice substitution precedes null widening**
  (229-234) — so Decision 9's "for free" claim holds.
- **`_build_annotations`** — consumer-authored and suppressed-pk both `continue` past `convert_scalar`
  (`base.py:943-958`), as Decision 7/8 assume.
- **`DjangoTypeDefinition`** — has `origin` (`definition.py:73`, the attribute Slice 2 reads),
  exactly four `consumer_*_fields` frozensets, `filterset_class`/`orderset_class`, and `finalized`
  (flipped in `finalizer.py:264` after `strawberry.type(...)`, Phase 3 — matches Decision 4).
  `FieldMeta` carries everything the inspect table prints (`field_meta.py:94-105`).
- **Registry** — `iter_types()` and `model_for_type()` exist with the cited signatures
  (`registry.py:211-235`); the one-primary-per-model rule is enforced in `registry.register`
  (131-137) and `finalizer._audit_primary_ambiguity` (117-142) — so the `Meta.primary` plumbing
  Slice 3 relies on is real.
- **`import_string` vs `import_module_symbol`** — the spec's reasoning is **correct**:
  `export_schema` uses `import_module_symbol` with `default_symbol_name="schema"`
  (`export_schema.py:35-38`), which resolves `module` or `module:symbol` but **not** a dotted
  *attribute* path like `apps.library.schema.BookType`. (The fakeshop `config.schema` test passes
  because the whole string is a module + default symbol, not because dotted attributes resolve.)
  Switching to Django's `import_string` for Slice 2 is the right call.
- **Fakeshop `Book`** — `title = TextField()` (non-null), `subtitle = TextField(blank=True, null=True)`,
  `circulation_status` CharField+choices (→ `BookTypeCirculationStatusEnum`), plus `shelf`/`genres`/
  `loans` relations — all present (`apps/library/models.py:97-112,162-165`). `scalars` baseline live
  tests exist. The Slice-3 acceptance-type approach (dedicated secondary type, don't mutate baselines)
  is the right isolation; note the existing BookType nullability baseline at
  `test_library_api.py:357-379` is exactly what you're protecting.
- **Glossary / CSV / PM docs** — all 23 glossary anchors the spec links resolve; the three net-new
  symbols are correctly absent from both the glossary and the companion CSV; `check_spec_glossary.py`
  validates only CSV terms against headings (so it stays green); the KANBAN card body genuinely
  contains every conflict the spec reconciles (stale `spec-021-…-0_0_8.md` ref, `## [0.0.8]` CHANGELOG
  text, `test_commands.py` path, `type_dotted_path` note); sibling cards 030/031/032 and `DONE-021-0.0.7`
  exist; spec-028 Decision 10 establishes the maintainer-commanded-bump precedent Decision 11 extends.

---

## Suggested edit map (where the P1s land)

- **Decision 3** (lines 270-295): rewrite the mechanism around 0.316.0's `get_extensions`; add the
  singleton-factory option (P1.3); drop the "sync is fine with the bare class" reasoning (P1.1).
- **Slice 1 test plan** (line 501) + **DoD item 4** (line 598): correct the no-warning claim; state
  the warning-handling decision (P1.2).
- **Current state** (line 114), **Problem statement** (line 97), **Borrowing** (line 141),
  **Risks** (lines 569-570): replace `_sync`/`_async` framing; pin to the locked version.
- **Decision 4** (line 305) + example (lines 191-200) + Slice-2 tests: add the suppressed-pk
  contract (P2.1), fix the BookType/GlobalID example (P2.2), resolve cold-invocation finalization
  (P2.3).
- **Slice 3 / Test plan**: add the schema-wide-assertion verification step (P2.4).
