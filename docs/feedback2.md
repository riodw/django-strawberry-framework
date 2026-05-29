# Review — `django_strawberry_framework/filters/` (branch `build-021-filters-0_0_8`)

## Method

Reviewed the full filter subsystem as it stands on this branch, driving coverage
with the two (just-collapsed) review scripts:

- `scripts/review_historical_package_snapshot_at_commit.py HEAD --package-dir django_strawberry_framework/filters`
  → stripped/overview shadow of all four modules at HEAD.
- `scripts/review_changed_python_diffs_against_head.py 039c4425` (branch fork point)
  → per-file diffs of everything this branch added (`base.py` +414, `factories.py`
  +302, `inputs.py` +967, `sets.py` +1359 lines).

Both scripts ran clean; the source files themselves were the source of truth for
the findings below. Gates checked: `ruff check` / `ruff format --check` on the
package both PASS.

## Scope note

`docs/feedback.md` scopes the *shipped* delta to `HIDE_FLAT_FILTERS` and explicitly
defers the row-security / permission cascade to `TODO-ALPHA-027-0.0.10`
(`apply_cascade_permissions`, a write-once `get_queryset` cascade). Several findings
below land inside that deferred permission subsystem — they are flagged as input to
that rework rather than as new regressions, since the branch is unfinished.

Overall: the code is unusually well-documented and the prior review rounds (R2–R5)
clearly closed a lot. The new `HIDE_FLAT_FILTERS` work is clean. The findings are
mostly in the permission pipeline (already slated for rework) plus a few coverage
gaps and nits.

---

## Findings

### 1. [Medium] Nested related branches run permission checks twice, and before the parent's own gate

`apply_sync` / `apply_async` derive each active branch's visibility queryset by
calling the **child filterset's full `apply_sync`** (`sets.py:775` / `:796`). That
call fires the child's `check_*_permission` gates and validates its form
(`sets.py:1283` / `:1300`). The parent's *own* later
`_run_permission_checks(input_value, request)` then **recurses into the same child
branch** (`sets.py:919-924`) and fires the child gates a second time.

The two pathways allocate independent `_fired` dedup maps (the nested `apply_sync`
starts a fresh `_fired=None`; the parent recursion threads its own), so the per-class
dedup at `sets.py:896-898` cannot span them. Consequences:

- **Double-fire of child gates.** Harmless for a pure boolean gate; a real defect for
  any gate with side effects (audit log, rate-limit counter, metrics) — it records
  twice. With depth-N related nesting a leaf gate fires O(N) times.
- **Ordering.** Child queryset evaluation + child gates run during *visibility
  derivation* (step 2 of the pipeline), i.e. **before** the parent's per-branch
  authorization gate `check_<rel>_permission` runs (step 6). A parent gate meant to
  forbid access to the relation cannot prevent the child-side work / information
  exposure that already happened.

This is squarely in the cascade slated for `TODO-ALPHA-027`. Recommendation for that
rework: derive visibility through a **permission-free** child path (run only
`get_queryset` + nested-leaf narrowing, not the child's gates/form), and run the
parent's per-branch gate **before** child evaluation. (`sets.py:743-797`, `:1263-1302`)

### 2. [Low] `check_permissions` back-compat shim reintroduces the per-lookup gate-name bug

`check_permissions` (`sets.py:1038-1058`) routes `self.data` — already-flattened
`django-filter` form keys like `name__icontains` — through `_run_permission_checks`.
`_active_permission_field_paths` then has no `_field_specs` entry for `name__icontains`
and falls through to `_form_key_for_python_attr`, building
`check_name_icontains_permission`. That is exactly the per-lookup dispatch the H2 fix
removed from the main GraphQL path (which correctly keys on `django_source_path`, so
`check_name_permission` fires once across all lookups — see `sets.py:902-913`,
`:991-1036`). Only this cookbook-compat delegate regresses. Either normalize the
form-keys back to source fields before dispatch, or document that this entry point
gates per-form-key by contract.

### 3. [Low / perf] `_normalize_input` is recomputed several times per `apply`

It runs in `apply_sync` (`sets.py:1278`), again inside `_run_permission_checks`
(`sets.py:901`), and again per logical branch in `_q_for_branch` (`sets.py:1184`).
Inside `_run_permission_checks` the full normalize is done **only** to read the three
`and`/`or`/`not` keys (`sets.py:936-957`) — it could read `and_`/`or_`/`not_` straight
off the input via the existing `_LOGIC_KEYS`, skipping a full-field normalize on the
hot path. Minor, but it compounds with finding #1's redundant traversals.

### 4. [Low] `_unwrap_enum_member` duck-types instead of checking the enum type

`inputs.py:469-477` returns the wrapper object whenever `member_value is None`, so an
enum member whose `.value` is legitimately `None` passes through un-unwrapped. Django
`TextChoices`/`IntegerChoices` won't hit this, but the guard is value-truthiness +
`hasattr(value, "name")` rather than a structural `isinstance(value, enum.Enum)`.
Consider keying on the enum type to remove the duck-typing edge.

### 5. [Coverage] `HIDE_FLAT_FILTERS` tests cover only the single-hop case

`tests/filters/test_inputs.py:772-829` assert on `_build_input_fields` triples for a
one-hop `shelves_code`. Worth adding before the branch closes:

- **Deep traversal** (`entries__property__category__name`) is hidden — the skip at
  `inputs.py:668` keys on `top_name.split("__", 1)[0] in related_filters`, which the
  current tests don't exercise past one level.
- **An explicitly-declared `__`-containing filter that is NOT a RelatedFilter child
  stays visible** — the same guard intentionally leaves those alone (no nested
  alternative exists), and that branch is untested.
- **A schema-introspection / live test** proving the field actually disappears from
  the composed GraphQL input type. The current tests stop at the triple list, not the
  built schema; given the toggle is the freshest delta, a schema-level assertion would
  lock the contract end-to-end.

### 6. [Nit] `_iter_filterset_subclasses` growth is documented but unmetered

`inputs.py:903-927` walks `type.__subclasses__()`; the docstring already flags that
long-running fixture-heavy suites accumulate filterset classes. Fine as-is for now —
noting it so it isn't lost when the deferred work touches the clear path.

---

## What's solid (kept deliberately short)

- **`HIDE_FLAT_FILTERS` implementation is cleaner than upstream**: a single `continue`
  in the grouping loop (`inputs.py:660-669`) replaces upstream's throwaway trimmed
  subclass, and the hidden operator-bag classes are never built — matching the
  efficiency claim in `feedback.md`. Nested-branch + scalar shapes are correctly
  untouched in either toggle position.
- **Form-field mapping order** is correct and well-explained: `DecimalField`/`FloatField`
  matched before `IntegerField` because they subclass it in `django.forms`
  (`inputs.py:211-221`).
- **GlobalID type-name preservation** through normalize (`inputs.py:446-466`) — re-encoding
  the `relay.GlobalID` object to its wire string so `filter()` can validate `type_name`
  before decoding — is a genuine correctness fix with a clear rationale.
- **`_logic_depth` hand-off** across `django-filter`'s `.qs` boundary (`sets.py:1186` →
  `:1110`) is a clever, well-documented answer to not owning `BaseFilterSet`.
- **`_lookups_for_field_class_cache`** keyed by field class with copy-on-return
  (`sets.py:52`, `:93`) is correct and needs no clear hook, as documented.
- **Cycle safety**: BFS `seen` gate (`factories.py:140`) and input-bounded recursion
  throughout; the `_MAX_LOGIC_DEPTH` `ClassVar` cap (`sets.py:197`) turns pathological
  nesting into a typed `ConfigurationError` instead of `RecursionError`.

## Scripts under test

The collapse works: the snapshot script produced 4 stripped+overview shadows for the
filters package into `docs/shadow/current/`; the diff script produced per-file diffs
into `docs/shadow/{old,new,diff}/` using the imported `_materialize_and_inspect`
primitive. Each script clears only its own folder, so the two coexist without
clobbering. No tracked file dirtied (`docs/shadow/` is gitignored).
