# Build: Slice 3 — code gaps escalated by the `spec-039` audit rollup

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
Rationale companion: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`
Build plan: `docs/builder/build-039-serializer_mutations-0_0_13.md`
Status: final-accepted

Four items, dispatched by Worker 0 from the four audit artifacts and verified against
`HEAD` before dispatch. This slice writes `.py` files only. **No spec edit lands here** —
Slice 2 owns every spec and rationale rewrite and runs after this slice is
`final-accepted`; everything this plan surfaces for the spec is parked under
`### Notes for Worker 1 (spec reconciliation)`.

---

## Plan (Worker 1)

### Slice declarations

**Files this slice owns.** Named exhaustively, because Slice 2 takes `resolvers.py`
only after this slice is `final-accepted` and an unnamed file is a collision:

- `django_strawberry_framework/rest_framework/resolvers.py` (item 2 — the only production edit)
- `tests/rest_framework/test_resolvers.py` (items 1, 2, 4)
- `tests/rest_framework/test_dry_import_ratchet.py` (item 3 — **new file**)
- `examples/fakeshop/test_query/test_products_api.py` (item 1, live half)

**Files this slice reads but never edits.** `tests/forms/test_resolvers.py` (the `038`
model for item 1), `examples/fakeshop/test_query/test_scalars_api.py` and
`examples/fakeshop/test_query/README.md` (the tier precedent),
`django_strawberry_framework/rest_framework/inputs.py`,
`django_strawberry_framework/rest_framework/serializer_converter.py`,
`django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/utils/converters.py`,
`django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/mutations/inputs.py`
(item 3's manifest sources).

**Files mutated transiently during failability proofs, never edited.**
`django_strawberry_framework/optimizer/walker.py` (item 1's proof) and
`django_strawberry_framework/rest_framework/inputs.py` (item 3's proof). Each is restored
from a pre-mutation copy under a scratch root **outside the repository** and the restore
proved by byte comparison. Neither appears in `### Files touched`.

**Baseline-dirty, out of scope — do not edit, do not revert** (`AGENTS.md` rule 34,
build plan `## Baseline-dirty, out-of-scope files`): `docs/feedback.md`; everything under
`docs/builder/` without `039` in its name; and the concurrent `spec-050` cycle's dirty
package and test files, which at plan time were `_strawberry_patches.py`, `apps.py`,
`conf.py`, `connection.py`, `list_field.py`, `orders/sets.py`, `resource_policy.py`,
`utils/querysets.py`, `tests/base/test_conf.py`, `tests/orders/test_sets.py`,
`tests/test_apps.py`, `tests/test_list_field.py`, `tests/test_resource_policy.py`,
`tests/test_strawberry_patches.py`, `tests/utils/test_querysets.py`, plus
`KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `examples/fakeshop/db.sqlite3`
and the `spec-050` docs. **None of this slice's four owned files was dirty at plan time**,
so every grade below is against `HEAD` content read via `git show HEAD:<path>` into a
scratch path outside the repo. `git stash`, `git checkout`, `git restore`, and
`git worktree` are banned for the whole slice.

#### Hot-path declaration

**This slice IS hot-path, and item 2 is the reason.** `_assert_field_agreement` is the
per-field body of `_assert_schema_runtime_agreement`, which runs once per write-surface
field on **every** `SerializerMutation` resolve, immediately before `is_valid()`
(`rest_framework/resolvers.py::_guarded_serializer_write` #"_assert_schema_runtime_agreement(mutation_cls, serializer)").
That is per-request, per-resolver, per-field — hot by `docs/builder/BUILD.md`
`## Hot-path budget`'s definition, and the section is explicit that a three-line diff
inside a loop over a write surface is still hot-path. The edit is expected to be
*cheaper* (two `getattr`-with-default calls retire in favour of direct attribute reads,
one `is None` identity test is added), but "expected cheaper" is not a number and the
section exists to stop exactly that reasoning standing in for one.

**Worker 2 owes a before/after number.** Two metrics, both stated and reproducible:

1. **Wall-clock, median per call.** `timeit.repeat(..., repeat=5, number=20_000)` over a
   single `_assert_schema_runtime_agreement(fake, serializer)` invocation built from the
   file's own `_agreement_specs_with_meta(SimpleNamespace(operation="create", model=library_models.Shelf, optional_fields=()), required=True)`
   plus `_shelf_model_serializer()`; report `statistics.median` of the five per-loop
   times, in microseconds, to three significant figures. Driver script under
   `docs/builder/temp-tests/039-slice-3/hotpath.py`, quoted in the build report.
2. **Structural count, per field.** Attribute accesses on the requiredness/annotation
   tail: before = 3 `getattr(..., <default>)` calls (`_mutation_meta`, `operation`,
   `optional_fields`); after = the number the diff actually leaves. Count them from the
   diff, not from this sentence.

**Order matters:** run metric 1 *before* the item-2 edit, then again after, in the same
process-fresh shell on the same machine. A single-shot reading is not a number.

#### Floor-verification scope

Item 2 edits `django_strawberry_framework/rest_framework/resolvers.py`, the DRF /
Strawberry integration seam, and item 1's live half asserts against **emitted SQL text**,
whose column-list formatting is a Django-version-sensitive surface. The build plan's own
declaration already anticipated this ("Slice 3, if it lands, re-declares …").

- **Floor versions, copied from `docs/builder/BUILD.md` `## Floor verification`, which is
  the single canonical statement of them:** Django **5.2.16**, Python **3.10**,
  strawberry-graphql **0.316.0**.
- **Focused scope at the floor** — not a second full sweep:
  - `tests/rest_framework/test_resolvers.py`
  - `tests/rest_framework/test_dry_import_ratchet.py`
  - `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
- **Owning pass: Worker 2's build pass.** Recorded in the build report's
  `### Floor verification` subsection with the scratch venv path (outside the repo), the
  resolved versions as read by `uv pip list --python <venv>/bin/python`, and each
  command's pass/fail. The `## Final test-run gate` is the backstop that confirms it
  happened, not a second owner.
- Build it per `docs/builder/BUILD.md` `### How to build the floor venv` with an explicit
  `--python`; **never install into the shared `.venv`**. `djangorestframework` is a soft
  dependency and is not in `[project].dependencies` — confirm `--group dev` brought it in
  before reading a pass as meaningful, or every `rest_framework` module skips and the run
  proves nothing.
- No `--cov*` flag anywhere; `--no-cov` only.

#### Boundary count and the split question

`docs/builder/BUILD.md` `### Slice splitting`, answered in writing as
`docs/builder/worker-1.md` `### Boundary count is a split trigger` requires.

Enumerated new **production** boundaries this slice adds: **one** — item 2's
`if meta is None: raise ConfigurationError(...)` in
`rest_framework/resolvers.py::_assert_field_agreement`. Items 1, 3, and 4 add or rewrite
assertions and add no production guard, cap, rejection path, or validation branch. The
production diff is one file and roughly six lines.

**Verdict: do not split.** One boundary, one production file, and the four items share a
single review surface (`tests/rest_framework/test_resolvers.py` is touched by three of
them), so splitting would create the parallel-cohort shared-shape problem the DRY section
warns about for no reduction in review load.

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** at plan time —
`django_strawberry_framework/` recursively, 2,061 lines, written to
`docs/shadow/039-helper-inventory.md` (039-stamped rather than the unprefixed name, so it
cannot collide with the concurrent `spec-050` session's scratch). Shapes searched:
`config_error` / `configuration_error` / `_error_message` / `prefix` (item 2's error
construction), `identity` / `manifest` / `promoted` / `shared_site` (item 3's ratchet),
`mutation_meta` / `require_meta` / `validated_meta` (item 2's accessor).
`scripts/review_inspect.py django_strawberry_framework/rest_framework/resolvers.py
--output-dir docs/shadow` was also run (the file is 2,421 lines, well past the 150-line
trigger in `docs/builder/BUILD.md` `### When to run the helper during build`).

Relevant candidates found:

- **No `_mutation_meta` accessor helper exists anywhere in the package.** The two hits are
  `auth/mutations.py::_AuthMutationMetaSnapshot` (a duck-typed *shape*, not an accessor)
  and `auth/mutations.py::_SealedAuthHolderMeta` (a rebind seal). Every one of the ~20
  read sites dereferences `mutation_cls._mutation_meta.<attr>` directly.
- **No shared `ConfigurationError` message builder exists.** Audit-3's DRY finding 1 (40
  repeated `"SerializerMutation "` prefixes in this one module) is real and is explicitly
  routed to the maintainer as a spec-independent cleanup card, not to this cycle.
- **One cross-module identity-assertion precedent exists**:
  `tests/utils/test_inputs.py::test_filter_and_order_input_namespaces_ride_make_set_input_namespace`
  — `filter_inputs._input_type_name_for is set_input_type_name` plus
  `filter_inputs._materialize_input.__code__ is order_inputs._materialize_input.__code__`.
  That is exactly the shape item 3 needs; item 3 reuses the pattern (bound-object identity
  for imports, `__code__` identity for factory-produced closures) rather than inventing one.
- **One source-grep-guard precedent exists** in the target file:
  `tests/rest_framework/test_resolvers.py::test_resolvers_source_has_no_live_strategy_reads_grep_guard`.
  It is a *negative* source grep and is **not** the model for item 3 — see below.

**Existing patterns reused.**

- Item 1, package half: `tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_suppresses_only`
  (`tests/forms/test_resolvers.py:2129-2162`) is the exact assertion shape — capture
  `ctx.dst_optimizer_plan` off a `context_value=SimpleNamespace()` handed to
  `schema.execute_sync`, then assert `plan.select_related` **and** `plan.only_fields`.
  Both halves are load-bearing: `select_related == ("category",)` is what proves the
  captured plan IS the re-fetch plan, since `DST_OPTIMIZER_PLAN` is documented last-wins
  introspection data (`django_strawberry_framework/optimizer/extension.py` #"``DST_OPTIMIZER_PLAN`` stays LAST-WINS introspection data").
- Item 1, live half: the assertion rewrite consumes `sql` / `item_selects`, both **already
  in scope** in the existing test (`examples/fakeshop/test_query/test_products_api.py:4402-4419`).
  No new capture machinery.
- Item 2: the module's own `ConfigurationError` idiom —
  `f"SerializerMutation {mutation_cls.__name__}: …"` followed by what to change — used by
  every raise in the file, including the four other arms of this same function.
- Item 3: `tests/utils/test_inputs.py:426-433`, as above.
- Item 4: `tests/rest_framework/test_resolvers.py::test_merged_kwargs_override_different_request_object_is_configuration_error`
  (`tests/rest_framework/test_resolvers.py:790-847`) is the twin the new row mirrors, and
  `::test_merged_kwargs_merges_override_context_keys_keeping_framework_request`
  (`:670-727`) supplies the hook-override class shape. The new row differs from the
  rejection twin in exactly one expression.

**New helpers justified.**

- **One**: item 3's manifest constant in `tests/rest_framework/test_dry_import_ratchet.py`
  — a module-level tuple of `(module, symbol, shared_module)` rows plus a second tuple of
  `(module, symbol, twin_module)` closure rows, consumed by two
  `@pytest.mark.parametrize` decorations. Single responsibility: *name the population the
  ratchet covers, in one place a reader can audit against the source*. It serves the
  ratchet's two test functions and nothing else.
- **None for item 2.** A `_require_mutation_meta(mutation_cls)` helper would have exactly
  one call site, because the other four `_mutation_meta` reads in this module are already
  direct dereferences that fail loud on their own. Extracting a one-call-site accessor
  would add an indirection layer over an attribute read on the request path. **Condition
  that would justify it later:** a second site needing the *same* `ConfigurationError`
  message rather than a bare `AttributeError` — most plausibly if the schema-time bind
  ever calls the agreement guard before the metaclass has stamped the snapshot.
- **None for item 1's schema harness.** `tests/rest_framework/test_resolvers.py` has no
  optimizer-extension schema builder (measured: no `DjangoOptimizerExtension` import, one
  `context_value=` use, at `:4481`, unrelated). The new plan-shape row declares its
  schema inline with `extensions=[lambda: DjangoOptimizerExtension()]`, matching the ~20
  other tests in the file that declare their schemas inline. **Condition that would
  justify extracting an `_optimizer_schema(...)` helper later:** a second plan-shape row
  in this file — the update re-fetch, or the delete snapshot's `force_load=True` plan.
  A helper shared across `tests/forms/` and `tests/rest_framework/` is explicitly
  **rejected**: it would be new cross-package test surface for one call site each, and the
  two flavors' schema fixtures differ (the form file's `_schema` also disables the
  `spec-048` error policy, which the serializer row does not need).

**Duplication risk avoided.**

1. **A second, half-populated import guard.** The obvious naive shape is one grep test in
   `tests/rest_framework/test_converter.py` and another in `test_inputs.py`, each covering
   its own module. That splits the manifest in two, and the two copies drift. The plan
   puts **one** manifest in **one** file covering **both** modules.
2. **A grep that re-spells what identity already proves.** Item 3 is specified as identity
   only. A source grep is satisfied by a same-named local and breaks on a legitimate
   import-style change; identity catches the redefinition *and* the deletion (an absent
   attribute raises), so a companion grep would be a second, weaker copy of the same check.
3. **A third `.only(...)` assertion.** Items 1's two halves assert **different** properties
   — emitted SQL columns (live) versus the plan object's fields (package) — and neither
   restates the other. The non-distinguishing live line is *replaced*, not supplemented,
   so the file does not end up with two live G2 assertions.
4. **A near-copy of the rejection test for item 4.** The new tolerance row reuses the
   rejection twin's mutation/schema scaffolding verbatim and differs only in the hook body
   and the assertion; it does not re-derive an independent fixture stack.

### Implementation steps

Line numbers below are **pin-at-write-time navigational hints** taken from `HEAD` content
read into a scratch path outside the repo. Verify against the current source before
editing — the concurrent `spec-050` session may have shifted a file since this plan was
written.

#### Item 2 first (it is the only production edit, and items 1/3's proofs mutate other files)

1. `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`,
   currently at `:1164-1170` (`HEAD`):

   ```python
   if spec.required is None and spec.annotation_repr is None:
       return
   meta = getattr(mutation_cls, "_mutation_meta", None)
   if meta is None:
       return
   operation = getattr(meta, "operation", "create")
   optional_fields = frozenset(getattr(meta, "optional_fields", None) or ())
   ```

   Replace the meta resolution with a boundary that **guards the answer**:

   - `meta = mutation_cls._mutation_meta` — a direct read, matching the four other
     `_mutation_meta` dereferences in this module (`:861`, `:1069`, `:1494`, `:2163`).
   - `if meta is None: raise ConfigurationError(...)` — the abstract-base spelling, which
     the current `getattr` default silently permits **identically** to the
     attribute-absent spelling. This is the whole point: the shipped guard enumerates one
     spelling of the incoherent input and lets the other through the same permit path.
     `docs/builder/BUILD.md` `### Fail-open shapes` is explicit that a guard written
     against an input spelling is a guess and a guard written against the answer is a
     boundary. The answer this tail computes is *"do the runtime field's requiredness and
     annotation agree with the schema's?"* — and with no validated snapshot it is
     undeterminable, so it must exit the permit path.
   - `operation = meta.operation` and `optional_fields = frozenset(meta.optional_fields or ())`
     — the two sibling `getattr`-with-default calls on the **same** four lines of the
     **same** decision path are the same catalogued shape. Fixing one and leaving two is
     the mistake this section documents. Keep the `or ()`: `optional_fields` is declared
     `tuple[str, ...] | None` and `None` and `()` are the same answer there, so it is not
     a fail-open; the `getattr` around it is.
   - Message shape: open `f"SerializerMutation {mutation_cls.__name__}: "`, state that the
     validated `Meta` snapshot is absent so requiredness and annotation agreement cannot be
     determined, and name it a framework invariant violation rather than a supported
     configuration. **No process provenance** (`START.md` `## Style Rio cares about`): no
     severity label, no round or slice number, no "previously".
   - Update the function docstring's closing sentence only if the edit falsifies it; the
     existing text ("Any divergence is a framework `ConfigurationError` at the boundary")
     already describes the new behavior.

   **Why this is the root-cause fix and not a test-only one** (`AGENTS.md`): the branch is
   **unreachable in production**, proved three ways at `HEAD`, and the production code — not
   the test — is what encodes the wrong abstraction.
   - `django_strawberry_framework/mutations/sets.py` #"_mutation_meta: _ValidatedMutationMeta | None = None"
     declares the attribute on the base class, so `getattr(mutation_cls, "_mutation_meta", None)`
     **never returns its default** for any class in the `SerializerMutation` MRO. The
     `getattr` default is dead on arrival.
   - `django_strawberry_framework/mutations/fields.py::_validate_mutation_target`
     #"if mutation_cls.__dict__.get(\"_mutation_meta\") is None:" rejects an abstract base
     at field construction, so a class with a `None` snapshot never gets a resolver and
     never reaches the write step.
   - Even setting both aside, `rest_framework/resolvers.py::_serializer_write_step`
     #"serializer_class = mutation_cls._mutation_meta.serializer_class" (`:2163`) and
     `::_injected_serializer_data` #"declared = frozenset(mutation_cls._mutation_meta.injected_fields or ())"
     (`:861`) dereference it unguarded and run **strictly before** the agreement guard at
     `:2258`. An absent-or-`None` snapshot raises `AttributeError` there, never reaching
     `_assert_field_agreement`.

   The only thing that reaches the branch is the hand-built fake in the package test.

2. Invert `tests/rest_framework/test_resolvers.py::test_agreement_guard_stops_when_mutation_meta_absent`
   (`:1313-1323`). Rename it so its name states the boundary rather than the retired
   permit ("stops when" → a name naming the rejection), and rewrite the body and docstring
   to assert the `ConfigurationError`. The docstring's current claim — "the tail needs the
   mutation's operation and model to say anything at all, so it stops instead of guessing
   an operation" — is precisely the reasoning the fix retires; the replacement docstring
   states the invariant (a mutation reaching this guard without a validated snapshot is a
   framework invariant violation), never the history.
3. Add two further rows in the same block, so the boundary is not weakly pinned by a
   single assertion. `docs/builder/BUILD.md` `### Acceptance rule` makes 0-or-1 rows
   `revision-needed`, and `START.md` `## Instruments that lie` is explicit that a `for`
   loop inside one test is one node id — these must be separate test functions or
   parametrized cases, never a loop.

#### Item 1 — the G2 `.only(...)` contract, split across tiers

4. **Package half.** Add one row to `tests/rest_framework/test_resolvers.py`. Build a
   probe schema over a create `SerializerMutation` for `products.Item` with
   `extensions=[lambda: DjangoOptimizerExtension()]`, execute
   `mutation { … { node { name category { name } } errors { field } } }` via
   `schema.execute_sync(..., context_value=ctx)` where `ctx = SimpleNamespace()`, then:
   - `plan = ctx.dst_optimizer_plan`
   - `assert plan.select_related == ("category",)`
   - `assert plan.only_fields == ()`

   Both assertions, in that order, mirroring
   `tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_suppresses_only`.
   The `select_related` assertion is not decoration: `DST_OPTIMIZER_PLAN` is last-wins, so
   it is what proves the captured plan is the re-fetch plan and not some other plan from
   the same execution.
5. **Live half.** In `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`,
   replace the final assertion (`HEAD` `:4420-4423`):

   ```python
   # G2 NO `.only(...)` projection: the post-write re-fetch selects the full item
   # row (no SQL names a strict deferred column subset), so the row reads back whole.
   assert "SerG2Widget" in models.Item.objects.values_list("name", flat=True)
   ```

   with an assertion **against the already-captured `sql` / `item_selects`** that the
   post-write re-fetch `SELECT` names at least one `products_item` column the GraphQL
   operation never selected. The operation selects `node { name category { name } }`, so a
   `.only(...)` projection would carry roughly `id` / `name` / `category_id` and would
   **omit** `description`, `attachment`, `is_private`, `created_date`, `updated_date`
   (`examples/fakeshop/apps/products/models.py::Item`). Naming one of those columns in the
   re-fetch `SELECT` is therefore distinguishing in both directions, and it reads
   `captured` rather than issuing a fresh query.

   Rewrite the comment too. Its current text points at "the package mirror's job"; after
   step 4 the mirror exists, so the comment names it by
   `path::QualifiedName` (`AGENTS.md` "Source references"), with no line number.
6. The two neighbouring absolute query-count assertions (`len(captured) == 17`, and the
   `== 2` / `== 3` `products_item` / `products_category` `SELECT` counts, `:4396-4419`)
   **are not touched.** They distinguish batching and were derived from a real run; the
   finding is scoped to the `.only(...)` line alone.

#### Item 3 — the DRY import ratchet

7. Create `tests/rest_framework/test_dry_import_ratchet.py`. Home chosen per `AGENTS.md`
   test placement: the property is a package-structure invariant with no reachable line in
   `django_strawberry_framework/`, so no real `/graphql` query can earn it and the live
   tier does not apply. A **new file** rather than a split across `test_converter.py` and
   `test_inputs.py`, because the obligation spans both modules and one manifest is the
   whole point (see `### DRY analysis`, duplication risk 1). `AGENTS.md`'s "no new files"
   restriction applies to `tests/base/` only.
8. **The manifest is written from `HEAD`, never from the spec's `### Import manifest`.**
   Audit 1a found the manifest names three symbols that have since moved and one group
   never imported, so a guard written from it would fail on correct code. The population
   below was **measured** at `HEAD`, by importing both modules under
   `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop` and comparing each
   binding against its shared site; every row printed `identical=True`.

   **Table A — bound-object identity** (`getattr(module, sym) is getattr(shared, sym)`),
   18 rows:

   | module | symbol | shared site | spec promotion row |
   |---|---|---|---|
   | `rest_framework/inputs.py` | `InputFieldSpec` | `utils/inputs.py` | P2.1 |
   | `rest_framework/inputs.py` | `make_input_namespace` | `utils/inputs.py` | P2.2 |
   | `rest_framework/inputs.py` | `make_shape_build_cache` | `utils/inputs.py` | P1.3 |
   | `rest_framework/inputs.py` | `get_or_store_shape_build` | `utils/inputs.py` | P1.3 |
   | `rest_framework/inputs.py` | `build_strawberry_input_class` | `utils/inputs.py` | P2.2 |
   | `rest_framework/inputs.py` | `pascalize_token` | `utils/inputs.py` | P2.3 |
   | `rest_framework/inputs.py` | `normalize_field_name_sequence` | `utils/inputs.py` | — |
   | `rest_framework/inputs.py` | `graphql_camel_name` | `utils/strings.py` | — |
   | `rest_framework/serializer_converter.py` | `convert_with_mro` | `utils/converters.py` | P1.4 |
   | `rest_framework/serializer_converter.py` | `make_kind_converter` | `utils/converters.py` | P1.4 |
   | `rest_framework/serializer_converter.py` | `make_scalar_converter` | `utils/converters.py` | P1.4 |
   | `rest_framework/serializer_converter.py` | `finish_field_conversion` | `utils/converters.py` | P1.4 |
   | `rest_framework/serializer_converter.py` | `InputFieldSpec` | `utils/inputs.py` | P2.1 |
   | `rest_framework/serializer_converter.py` | `SCALAR` | `utils/inputs.py` | kind enum |
   | `rest_framework/serializer_converter.py` | `FILE` | `utils/inputs.py` | kind enum |
   | `rest_framework/serializer_converter.py` | `RELATION_SINGLE` | `utils/inputs.py` | kind enum |
   | `rest_framework/serializer_converter.py` | `RELATION_MULTI` | `utils/inputs.py` | kind enum |
   | `rest_framework/serializer_converter.py` | `graphql_camel_name` | `utils/strings.py` | — |

   The four kind constants are in scope because `rest_framework/serializer_converter.py`
   itself states the contract in shipped source — #"single-sourced in ``utils/inputs.py`` (one conceptual enum," —
   and a re-spelled constant is exactly what identity catches and prose cannot.

   **Table B — closure `__code__` identity** for the P2.2 one-ledger trio, whose members
   are factory-produced closures and therefore cannot be object-identical across flavors.
   Both rows measured `True` at `HEAD`:

   | module | symbol | twin |
   |---|---|---|
   | `rest_framework/inputs.py` | `_materialize_input` | `mutations/inputs.py::_materialize_input` |
   | `rest_framework/inputs.py` | `_clear_input_namespace` | `mutations/inputs.py::_clear_input_namespace` |

   `make_shape_build_cache` has **no** cross-flavor `__code__` row: measured at `HEAD`,
   neither `mutations/inputs.py` nor `forms/inputs.py` uses it, so there is no twin. The
   Table A identity row on the factory itself is the whole obligation there.

9. Two `@pytest.mark.parametrize`d test functions, one per table — **parametrized, never a
   `for` loop**. `START.md` `## Instruments that lie`: a loop inside one test is one node
   id, and a ratchet whose failability is capped at 1 row is `revision-needed` on its own
   terms. 20 node ids total.
10. Each assertion is `getattr(module, sym) is getattr(shared, sym)` with a failure message
    naming the module, the symbol, and the shared site. An absent attribute must surface as
    a failure, not an error that reads as a collection problem — so resolve both sides with
    an explicit `pytest.fail` on a missing name, or assert membership in `vars(module)`
    first. A deletion-and-inline is as much a DRY regression as a redefinition, and this is
    the arm that catches it.
11. Module docstring states the invariant and names the manifest as the thing to edit
    deliberately when a symbol legitimately moves. No process provenance; the spec
    decision pointer (`spec-039` Slice 1 DRY / reuse) is a permitted citation per
    `START.md`.

#### Item 4 — the request-identity tolerance arm

12. Add one row to `tests/rest_framework/test_resolvers.py`, immediately after
    `::test_merged_kwargs_override_different_request_object_is_configuration_error`
    (`:790-847`). Same `SerializerMutation` + `DjangoMutationField` + `DjangoSchema`
    scaffolding, same `info = SimpleNamespace(context=SimpleNamespace(request=request))`,
    with the hook returning `kwargs["context"] = {"request": info.context.request}` — the
    framework's own request object echoed back, which is the realistic consumer shape (a
    hook building a DRF-style context). Assert **no raise** and
    `kwargs["context"]["request"] is request`.
13. That completes the pair `rest_framework/resolvers.py::_merged_serializer_kwargs`
    #"context['request'] object; the framework owns the request context (the actor" states
    in its own docstring: "a DIFFERENT object is a `ConfigurationError`, the SAME object
    tolerated". Only the rejection half was pinned. No production change.

#### Closing steps

14. `uv run ruff format <the four owned files>` then `uv run ruff check --fix <the same files>`
    — **scoped to this slice's own files, never `.`** (`docs/builder/ARTIFACT.md`
    `### Validation run`). Then `git status --short`: every modified file must be one of
    the four named above. Anything else is a **stop-and-report**, never a revert — this
    tree carries a concurrent session's uncommitted work.
15. Focused runs, no `--cov*` flag: `uv run pytest tests/rest_framework/ examples/fakeshop/test_query/test_products_api.py --no-cov`.
16. `uvx pre-commit run --files <the four owned files>` before handing to Worker 3 —
    `scripts/check_trailing_commas.py` owns single-line explosion and ASCII-only `.py`
    source, and ruff does not.

### Test additions / updates

| # | Path | What it pins | New/changed |
|---|---|---|---|
| 1 | `tests/rest_framework/test_resolvers.py` | the serializer G2 re-fetch plan: `plan.select_related == ("category",)` **and** `plan.only_fields == ()`, off `ctx.dst_optimizer_plan` | new |
| 1 | `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count` | the post-write re-fetch `SELECT` names a `products_item` column the operation never selected — read off the already-captured `sql`, not a fresh query | **rewritten** (the replaced line was non-distinguishing) |
| 2 | `tests/rest_framework/test_resolvers.py::test_agreement_guard_stops_when_mutation_meta_absent` | inverted: `_mutation_meta` **attribute absent** now raises `ConfigurationError` | **rewritten + renamed** |
| 2 | `tests/rest_framework/test_resolvers.py` | `_mutation_meta` present but **`None`** (the abstract-base spelling) raises `ConfigurationError` | new |
| 2 | `tests/rest_framework/test_resolvers.py` | the boundary fires on the **annotation** axis too, not only requiredness: a spec carrying `annotation_repr` with `required=None` and no snapshot raises | new |
| 3 | `tests/rest_framework/test_dry_import_ratchet.py` | Table A — 18 parametrized bound-object identity rows | new file |
| 3 | `tests/rest_framework/test_dry_import_ratchet.py` | Table B — 2 parametrized closure `__code__` identity rows | new file |
| 4 | `tests/rest_framework/test_resolvers.py` | a hook echoing the framework's **own** request object is **permitted**, and the framework request still wins | new |

Item 2's three rows are deliberately three, not one: the fix converts a permit path into a
rejection path, and `docs/builder/BUILD.md` `### Acceptance rule: weakly pinned is
revision-needed` makes a 0-or-1-row boundary unacceptable. Both incoherent-input spellings
(attribute absent, attribute `None`) must fail, because the shipped code permitted both
through the same expression — pinning only one would reproduce the original defect in the
test suite.

**Temp-test opportunities for Worker 3.** Worker 3 may write a temp test under
`docs/builder/temp-tests/039-slice-3/` to demonstrate that the *replaced* live assertion
was non-distinguishing — construct the pre-fix line, mutate
`optimizer/walker.py::_enable_only_for_operation` to `return True`, and show the old line
still passes while the new one fails. That is the cleanest independent confirmation that
item 1 actually closed the finding rather than moving it.

#### Failability proofs

`docs/builder/BUILD.md` `## Failability proofs` — which items owe one, stated so Worker 2
is not left guessing. Use `uv run python scripts/prove_failability.py
docs/builder/temp-tests/039-slice-3/proofs.json --scratch-root <a path OUTSIDE the repo>
--output <...>`; it is the supported way and it fills every measured field including the
mandatory pre-mutation baseline. Read its `--help` for the manifest schema and flag list —
this plan does not restate them.

- **Item 2 — proof REQUIRED.** A new rejection path. Mutation: restore the fail-open by
  replacing the `raise` with `return`. Anchor: a distinctive substring of the new error
  message (Worker 2 pins it after the code lands; `--check-anchors-only` first, and it
  must match **exactly once**). Scope: `tests/rest_framework/test_resolvers.py`. Expected
  ≥ 3 rows (the three item-2 tests). Label:
  `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`.
- **Item 1 — proof REQUIRED**, even though it adds no production boundary. The finding
  *is* "the assertion cannot fail", and the only acceptable evidence that the replacement
  can is the mutate / run / list-node-ids / revert / byte-compare loop. Mutation:
  `django_strawberry_framework/optimizer/walker.py::_enable_only_for_operation` — anchor
  `    return operation is None or operation is OperationType.QUERY` (**verified: exactly
  1 occurrence at `HEAD`**), replacement `    return True`, which reinstates `.only(...)`
  under a `MUTATION` and so removes the G2 boundary both new assertions claim to pin.
  Scope: `tests/rest_framework/test_resolvers.py examples/fakeshop/test_query/test_products_api.py`.
  Expected ≥ 2 rows, and **both** the new package row and the rewritten live row must
  appear in the failing set — if either does not, that assertion is still
  non-distinguishing and the item is not closed. Keep `tests/forms/test_resolvers.py` out
  of the scope: its G2 row is a pre-existing pin, not this slice's boundary, and including
  it only inflates the count.
- **Item 3 — proof REQUIRED.** A ratchet whose failability is unproven is an instrument
  that cannot fail. Mutation in `django_strawberry_framework/rest_framework/inputs.py`,
  anchored on the **tail** statement
  `_serializer_shape_build_cache, clear_serializer_shape_build_cache = make_shape_build_cache()`
  (verified: exactly 1 occurrence at `HEAD`; the file is 1,812 lines and this sits at
  `:1807`). Append three same-named local re-bindings that wrap the promoted objects with
  behaviorally identical delegating functions — e.g.
  `_promoted = pascalize_token` then `def pascalize_token(token): return _promoted(token)`,
  and the same for `make_input_namespace` and `make_shape_build_cache`. Anchoring at the
  tail matters: every call site of all three runs earlier in the module, so the re-binding
  is inert at runtime and **only the ratchet sees it** — which is exactly the regression
  shape (a same-named local with an equivalent body) the guard exists to catch, and the
  reason a wall-clock-free identity check is the right instrument. Scope:
  `tests/rest_framework/`. Expected ≥ 3 rows, all in
  `test_dry_import_ratchet.py`; a collateral failure elsewhere means the wrapper was not
  behavior-preserving and the mutation must be narrowed and re-run.
- **Item 4 — NO proof owed.** It adds one assertion to an existing, unchanged rejection
  boundary whose rejecting arm is already pinned. `docs/builder/BUILD.md`
  `### What needs a proof, and what does not` scopes the obligation to new boundaries.

Every entry: one mutation live at a time, reverted before the next begins, restore proved
by byte comparison, scratch root **outside** the repository. Never leave a mutation across
a `Status:` transition and never hand a mutated tree to Worker 3.

### Implementation discretion items

Choices assessed and decided to be Worker 2's:

- The exact wording of item 2's `ConfigurationError` message, subject to two fixed
  constraints: it opens `f"SerializerMutation {mutation_cls.__name__}: "` (the module's
  40-site convention) and it carries no process provenance.
- The new test function names, subject to the file's existing naming shape and to naming
  the invariant rather than the retired behavior.
- Which `products_item` column item 1's live assertion anchors on, and how it identifies
  the re-fetch `SELECT` within `item_selects`. **Derive it from a real run** — read the
  captured SQL and pick the anchor; `docs/builder/BUILD.md` forbids guessing a query-shape
  value. If the re-fetch is not the last `products_item` `SELECT`, say so in
  `### Implementation notes` and anchor differently.
- The `ids=` spelling of both parametrizations in `test_dry_import_ratchet.py`, and
  whether the two tables are two module-level tuples or one tuple with a discriminator.
- Where in `tests/rest_framework/test_resolvers.py` the new plan-shape row sits (its own
  commented section versus beside the agreement-guard block).
- The `SerializerMutation` fixture item 1's package row builds on — a fresh minimal
  declaration or a reuse of `_bind_item_serializer_mutation` / `_basic_item_serializer`.
  Either is fine provided the schema carries the optimizer extension and the operation
  selects `node { name category { name } }`.

Not discretion, and settled here: item 1's tier split (both halves, for the stated
reasons); item 3's home, population, and identity-not-grep shape; item 2 raising rather
than returning, and the two sibling `getattr` defaults going with it.

### Dispatched findings checklist

One box per finding dispatched to this cohort, quoting the finding as the audit stated it
and citing the symbol-qualified path Worker 0's verification recorded. Boxes stay `- [ ]`
at planning; **Worker 2 ticks `- [x]` only a box whose fix actually landed in its diff.**

- [x] **High — the G2 "no `.only(...)`" claim has no distinguishing assertion.** Audit 1c,
  High-1: *"the G2 'no `.only(...)`' contract has no distinguishing assertion anywhere …
  That line issues a fresh ORM query against the database and never reads `captured` or
  `sql`. It passes identically whether the re-fetch applied `.only(...)` or not — it only
  proves the row was written."* Verified at
  `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
  #"G2 NO `.only(...)` projection: the post-write re-fetch selects the full item". Model:
  `tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_suppresses_only`
  #"plan.only_fields == ()". Closes when **both** halves land (steps 4 and 5) and item 1's
  failability proof shows both in the failing set.
- [x] **Medium — a fail-open guard.** Audit 1c, Medium-1: *"`_assert_field_agreement` fails
  **open** when `_mutation_meta` is absent … A `getattr` default on a decision path
  converting 'cannot determine' into 'permit'."* Verified at
  `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`
  #"meta = getattr(mutation_cls, \"_mutation_meta\", None)". Closes when the branch raises,
  the two sibling `getattr` defaults on the same decision path are retired, and the three
  test rows land.
- [x] **Medium — the DRY import ratchet was never written.** Audit 1a, D6 (DROPPED): *"the
  DRY import guard the spec makes the DoD check was never built … No executable guard
  exists in any of the three places one could live."* The spec's obligation:
  `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` `## Slice checklist` → Slice 1 →
  `**DRY / reuse**` #"A grep guard that". Worker 0 verified the *contract holds* at `HEAD`
  — every promoted symbol has 0 definitions under `rest_framework/` — so this is a ratchet
  to add, not a repair. Closes when `tests/rest_framework/test_dry_import_ratchet.py`
  carries the HEAD-measured manifest as parametrized identity assertions and its
  failability proof passes.
- [x] **Low — the request-identity guard's tolerance arm is unpinned.** Audit 1d, Low-4:
  *"The 'same `context[\"request\"]` object is tolerated' arm has no test … the nearest
  rows return a `context` with **no** `\"request\"` key at all and then assert the
  framework's request won. So the guard's identity check is pinned only on its rejecting
  side."* Verified at
  `django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs`
  #"context['request'] object; the framework owns the request context (the actor"; the
  rejection twin is
  `tests/rest_framework/test_resolvers.py::test_merged_kwargs_override_different_request_object_is_configuration_error`.
  Closes when the one tolerance assertion lands.

### Notes for Worker 1 (spec reconciliation)

Carried forward to **Slice 2**, which owns every spec and rationale edit. Nothing here is
actioned in this slice.

1. **Spec status-line re-verification for this spawn** (`docs/builder/worker-1.md`): the
   spec carries no `Status:` line — it is archived under `docs/SPECS/` and opens "Shipped
   in `0.0.13` (card `DONE-039-0.0.13`)", which is accurate at `HEAD` and which nothing in
   this slice falsifies. No header edit owed. Recorded so the check is visibly performed
   rather than assumed.
2. **The DoD check's mechanism changes.** Slice 1's `**DRY / reuse**` bullet closes "A grep
   guard that `rest_framework/serializer_converter.py` + `rest_framework/inputs.py`
   **import** these and do not redefine them is the DoD check." This slice ships an
   **identity** guard, not a grep — a grep is satisfied by a same-named local and breaks on
   an import-style change. Slice 2 restates the sentence to name the shipped mechanism and
   its test path, stating the current contract with no chronology; the "why identity, not
   grep" reasoning belongs in the rationale companion under the same decision.
3. **The `### Import manifest` row for `resolvers.py`** (audit 1c, C4) is still stale and
   still Worker 1's choice between the three resolution paths that audit escalated. This
   slice deliberately did **not** write its guard from that manifest, and does not repair
   it. Unchanged obligation for Slice 2.
4. **Where the G2 plan-shape half lives.** After this slice the live test's "the package
   mirror's job" comment resolves to a real path. The spec's Slice-3 checklist and DoD
   item 4 currently imply the live tier carries the whole G2 contract. Slice 2 should state
   the split the `test_scalars_api.py` precedent already established repeatedly — behavioral
   half live, plan-state half package-internal — naming the package path by
   `path::QualifiedName`.
5. **`_assert_field_agreement`'s meta arm.** Audit 1c already recorded that rev6 #1 omits
   the requiredness-drift and annotation-`repr` drift arms entirely and cites
   `_assert_injected_field_agreement`, a symbol that does not exist. This slice adds a
   rejection to that same tail, so whatever Slice 2 writes for rev6 #1 must describe the
   raise, not a stop.
6. **Edge case 7 / Test plan — no change owed.** The tolerance arm the spec always
   specified is now pinned. Recorded so Slice 2 does not re-raise it as a gap.
7. **The build plan on disk carries none of the three sections the dispatch names.**
   Measured at plan time: `docs/builder/build-039-serializer_mutations-0_0_13.md` is
   8,876 B with nine headings, the last being `## Checklist` at `:133`; there is no
   `## Audit rollup`, no `## Worker-0 verification of every code-bearing finding`, and no
   `## Dispatch-order amendment`. This plan was therefore written from the dispatch text
   plus the four audit artifacts, and every code-bearing claim in it was independently
   re-verified against `HEAD` rather than accepted from the dispatch — which is how the
   symbol population for item 3 was caught diverging (see note 8). **Worker 0 should land
   those sections before the integration pass**: detail living only in a subagent's message
   is exactly the failure `docs/builder/BUILD.md` `### Cohorting, naming, and closure`
   names, and the cycle otherwise has no on-disk record of what was verified.
8. **Not a spec issue, but load-bearing for the record.** The dispatch named six promoted
   symbols for item 3 (`pascalize_token`, `make_input_namespace`, `build_and_stash_input`,
   `reject_unknown_meta_keys`, `normalize_field_name_sequence`, `visible_related_object`).
   Measured at `HEAD`, **three of those six are not bound in either target module**:
   neither `rest_framework/inputs.py` nor `rest_framework/serializer_converter.py` imports
   `build_and_stash_input`, `reject_unknown_meta_keys`, or `visible_related_object`. A
   guard written from that list would raise `AttributeError` on correct code — the same
   failure mode the dispatch warned about for the spec's own `### Import manifest`, in a
   second spelling. The manifest in step 8 is measured, not transcribed.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations.

- `django_strawberry_framework/rest_framework/resolvers.py` (M) — item 2, the only
  production edit. `::_assert_field_agreement`'s requiredness/annotation tail no longer
  fails open when the validated `Meta` snapshot is absent: the `return` became a
  `ConfigurationError`, and the two sibling `getattr`-with-default reads on the same
  decision path (`operation`, `optional_fields`) became direct attribute reads.
- `tests/rest_framework/test_resolvers.py` (M) — items 1 (package half), 2, and 4:
  three rows for the new rejection, one G2 plan-shape row plus its schema builder, one
  request-identity tolerance row, `optional_fields=()` added to the three existing
  `_agreement_specs_with_meta` fakes, `DjangoOptimizerExtension` added to the package
  import block, and the module docstring amended so its "no G2 test is duplicated here"
  claim stays true.
- `tests/rest_framework/test_dry_import_ratchet.py` (??, new) — item 3, the identity
  ratchet: 18 bound-object rows + 2 `__code__` rows, parametrized.
- `examples/fakeshop/test_query/test_products_api.py` (M) — item 1, live half: the
  non-distinguishing final assertion replaced by one that reads the already-captured SQL.

`django_strawberry_framework/optimizer/walker.py` and
`django_strawberry_framework/rest_framework/inputs.py` were mutated **transiently** during
failability proofs and restored; both are byte-identical to `HEAD`
(`git diff --stat` over the pair prints nothing) and neither is in this diff.

### Tests added or updated

- `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_missing_mutation_meta_snapshot`
  — a spec carrying a requiredness contract with the `_mutation_meta` attribute ABSENT
  raises. (Rewritten + renamed from `::test_agreement_guard_stops_when_mutation_meta_absent`,
  which asserted the retired permit.)
- `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_none_mutation_meta_snapshot`
  — the abstract-base spelling (`_mutation_meta` present but `None`) raises through the
  same rejection. New.
- `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_missing_snapshot_on_the_annotation_axis`
  — the rejection fires on the annotation axis too (`required=None`,
  `annotation_repr=repr(str)`), not only requiredness. New.
- `tests/rest_framework/test_resolvers.py::test_serializer_refetch_keeps_select_related_suppresses_only`
  — the serializer G2 re-fetch PLAN: `plan.select_related == ("category",)` (which is what
  proves the last-wins stash IS the re-fetch plan) **and** `plan.only_fields == ()`. New,
  with `_build_serializer_g2_schema` as its fixture.
- `tests/rest_framework/test_resolvers.py::test_merged_kwargs_override_echoing_the_same_request_object_is_tolerated`
  — a hook returning the framework's OWN `context["request"]` object is permitted and the
  framework request still wins. New; the rejecting twin above it was already pinned.
- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself`
  — 18 parametrized rows, `vars(consumer)[symbol] is vars(owner)[symbol]`. New file.
- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_closures_share_one_body`
  — 2 parametrized rows, `__code__` identity against the `mutations/inputs.py` twins. New file.
- `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
  — final assertion **rewritten**: the post-write re-fetch `SELECT` (the last real
  `products_item` `SELECT`) names `description` / `attachment` / `is_private` /
  `created_date` / `updated_date`, every column outside what a `.only(...)` projection for
  `node { name category { name } }` could carry. Reads `item_selects`, issues no query.
  The three neighbouring absolute count assertions were not touched.

### Validation run

- `uv run ruff format django_strawberry_framework/rest_framework/resolvers.py tests/rest_framework/test_resolvers.py tests/rest_framework/test_dry_import_ratchet.py examples/fakeshop/test_query/test_products_api.py` — **pass** (4 files left unchanged on the final run).
- `uv run ruff check --fix <the same four files>` — **pass** ("All checks passed!").
- `uv run python scripts/check_trailing_commas.py <the same four files>` — reformatted one
  construct (the `undeferred` tuple in the live test, >= threshold with no trailing comma);
  re-ran `ruff format` + `ruff check --fix` afterwards, then
  `check_trailing_commas.py --check <the four files>` — **pass**, exit 0.
- `git status --short` after both ruff invocations — the only entries naming this slice are
  the four files in `### Files touched`. Every other entry was already present at spawn
  time and is the concurrent `spec-050` cycle's work listed in the plan's baseline-dirty
  paragraph. **Nothing unexpected appeared, and nothing was reverted.**
- `uv run pytest -n0 tests/rest_framework/ examples/fakeshop/test_query/test_products_api.py --no-cov` — **pass**, 631 passed.
- `uv run pytest --no-cov` (full sweep, all trees) — **7 failed, 7629 passed, 40 skipped**.
  All seven are outside this slice: `tests/test_list_field.py` (4),
  `tests/utils/test_querysets.py` (1), `tests/orders/test_sets.py` (1),
  `examples/fakeshop/test_query/test_list_field_api.py` (1). See
  `### Notes for Worker 1 (spec reconciliation)` item 3 — recorded and escalated, not acted on.

### Failability proofs

Produced by `uv run python scripts/prove_failability.py docs/builder/temp-tests/039-slice-3/proofs.json --scratch-root <scratchpad>/failability --output docs/builder/temp-tests/039-slice-3/proofs.md`; run exit code **0** (every entry proved, none weakly pinned, no collection or setup error). Anchors were confirmed with `--check-anchors-only` first: all three matched exactly once. The scratch root is outside the repository; the run left no `ACTIVE-MUTATION.json` marker, and `git diff` over the two transiently-mutated files is empty.

- `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` —
  mutation applied: the whole `raise ConfigurationError(...)` for the missing validated
  `Meta` snapshot replaced by `return`, i.e. the fail-open this item retired, put back;
  scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/rest_framework/test_resolvers.py`;
  pre-mutation state of that scope: green (`172 passed`, pytest exit 0), 0 pre-existing
  failing rows differenced out; failing node ids:
  `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_missing_mutation_meta_snapshot`,
  `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_none_mutation_meta_snapshot`,
  `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_missing_snapshot_on_the_annotation_axis`;
  collection/setup errors: **0**; revert proved by byte comparison:
  `filecmp.cmp(shallow=False)` True and sha256 `384ea9a0bd4731ba...` == `384ea9a0bd4731ba...`
  against the pre-mutation copy.
- `django_strawberry_framework/optimizer/walker.py::_enable_only_for_operation` —
  mutation applied: `    return operation is None or operation is OperationType.QUERY`
  replaced by `    return True`, which re-enables `.only(...)` under a MUTATION and so
  removes the G2 property both halves of item 1 claim to pin (transient; the file is not
  in this slice's diff); scope as run:
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/rest_framework/test_resolvers.py examples/fakeshop/test_query/test_products_api.py`;
  pre-mutation state of that scope: green (`307 passed`, pytest exit 0), 0 pre-existing
  failing rows; failing node ids:
  `tests/rest_framework/test_resolvers.py::test_serializer_refetch_keeps_select_related_suppresses_only`,
  `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
  — **both halves are in the failing set**, which is the plan's stated closure condition
  for the item; collection/setup errors: **0**; revert proved by byte comparison:
  `filecmp.cmp(shallow=False)` True and sha256 `102a71658c211aa8...` == `102a71658c211aa8...`.
- `django_strawberry_framework/rest_framework/inputs.py::_serializer_shape_build_cache` —
  mutation applied: after the module's tail
  `_serializer_shape_build_cache, clear_serializer_shape_build_cache = make_shape_build_cache()`
  (past every call site, so the change is inert at runtime), `pascalize_token`,
  `make_input_namespace`, and `make_shape_build_cache` re-bound to same-named local
  delegating wrappers over the promoted objects — the redefinition shape the ratchet
  exists to catch; scope as run:
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/rest_framework/`;
  pre-mutation state of that scope: green (`496 passed`, pytest exit 0), 0 pre-existing
  failing rows; failing node ids:
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_input_namespace]`,
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_shape_build_cache]`,
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.pascalize_token]`
  — three ratchet rows and **no collateral failure**, which is the evidence the wrapper was
  behavior-preserving; collection/setup errors: **0**; revert proved by byte comparison:
  `filecmp.cmp(shallow=False)` True and sha256 `c97f01100b3bd840...` == `c97f01100b3bd840...`.

Item 4 owes no proof: it adds one assertion to an existing, unchanged rejection boundary
whose rejecting arm was already pinned. No entry is zero-row, so no **why 0** judgement is
owed anywhere in this subsection.

### Hot-path budget

Metric 1 — **wall-clock median per call, microseconds.** Driver:
`docs/builder/temp-tests/039-slice-3/hotpath.py`, run as
`uv run python docs/builder/temp-tests/039-slice-3/hotpath.py`. It builds the file's own
fake (one `SCALAR` `InputFieldSpec` with `required=True`, no `annotation_repr`) plus a
`_mutation_meta` of `SimpleNamespace(operation="create", model=library_models.Shelf, optional_fields=())`
and a `ModelSerializer` over `library.Shelf`, warms the lazy `serializer.fields` map, then
`timeit.repeat(lambda: _assert_schema_runtime_agreement(fake, serializer), repeat=5, number=20_000)`
and reports `statistics.median` of the five per-call figures. `required=True` matches the
runtime field, so the call reaches the meta tail and returns without raising — the tail the
edit sits in. Same machine, same shell, process-fresh each run; measured **before** the
item-2 edit and again after.

| Run | Before the edit | After the edit |
|---|---|---|
| first | **0.492 us** | **0.467 us** |
| repeat (noise gauge) | 0.464 us | 0.461 us |

Delta on the pinned first pair: **-0.025 us (-5.1%)**. Run-to-run spread on the unchanged
code was 0.028 us, so the delta is the same order as the noise — the honest reading is
"no measurable cost added, directionally cheaper", not a proven 5% win. Both figures are
recorded rather than one, so the maintainer can see the spread.

Metric 2 — **structural attribute-access count per field on the requiredness/annotation
tail**, read off the diff, not predicted:

| | Before | After |
|---|---|---|
| `getattr(..., <default>)` calls | 3 (`_mutation_meta`, `operation`, `optional_fields`) | **1** (`_mutation_meta` only) |
| direct attribute reads on `meta` | 0 | **2** (`meta.operation`, `meta.optional_fields`) |
| `is None` identity tests | 1 | 1 (unchanged; its arm changed from `return` to `raise`) |

Total attribute accesses per field is unchanged at 3; two of the three moved from a
defaulted `getattr` call to a direct read, which is the cheaper form and the reason the
wall-clock moved down rather than up.

### Floor verification

Owned by this build pass per the plan's floor-verification declaration. Versions taken from
`docs/builder/BUILD.md` `## Floor verification`, the single canonical statement of them.

- Scratch venv, **outside the repository**:
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/9b9a1987-25b1-40e6-9014-2cfab5f72707/scratchpad/dsf-floor`.
- Built as `uv venv <path> --python 3.10`, then
  `uv pip install --python <path>/bin/python -e . --group dev`, then
  `uv pip install --python <path>/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'`.
  Every install carried the explicit `--python`; **the shared `.venv` was not touched** —
  it still reports Django 6.1 / strawberry-graphql 0.324.0 after the run.
- Resolved versions, as read by `uv pip list --python <path>/bin/python`: interpreter
  **CPython 3.10.19**, `django` **5.2.16**, `strawberry-graphql` **0.316.0**,
  `djangorestframework` **3.18.0**, `django-filter` 26.1, `pytest` 9.1.1,
  `pytest-django` 4.14.0, `pytest-xdist` 3.8.0.
  `djangorestframework` is a soft dependency in `[dependency-groups].dev`, and its presence
  was confirmed **before** reading the result: without it every `rest_framework` module
  would skip and the run would prove nothing.
- Focused scope run:
  `<path>/bin/python -m pytest -n0 --no-cov -q tests/rest_framework/test_resolvers.py tests/rest_framework/test_dry_import_ratchet.py "examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count"`
  — **PASS**, `193 passed in 7.81s`, reported by pytest as
  `django: version: 5.2.16` on `platform darwin -- Python 3.10.19`. No `--cov*` flag.

Verdict: **pass** at Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0. The live G2
row's SQL-text assertion, which was the version-sensitive reason the plan scoped this run,
holds at the floor as well as at the ceiling.

### Implementation notes

- **The live G2 anchor was derived from a real run, not guessed.** The captured SQL was
  dumped through a transient `print` in the test under `pytest -s` and then removed. The 17
  queries carry exactly two real `products_item` `SELECT`s: the post-save FK attestation's
  single-column `values()` read (`SELECT "products_item"."category_id" AS "category_id" ...`)
  and, after it, the optimizer-planned re-fetch naming all eight columns. So the re-fetch
  **is** the last one, and the new assertion takes `[-1]` off the same `item_selects` list
  the neighbouring count assertions already build. Anchoring on five columns rather than one
  makes the row distinguishing in both directions: a `.only(...)` projection for
  `node { name category { name } }` could carry at most `id` / `name` / `category_id`, and
  the attestation read (which does name a strict subset) is excluded by position and would
  fail the assertion if it were ever picked up.
- **The three existing `_agreement_specs_with_meta` fakes gained `optional_fields=()`.**
  Retiring `getattr(meta, "optional_fields", None)` makes the attribute mandatory on any
  meta that reaches the tail, and those three `SimpleNamespace`s did not declare it. This is
  the fix restoring the tests' original intent against the current contract, not a weakened
  assertion — each still pins exactly what it pinned before.
- **The kind-constant identity rows have a known ceiling, and it is not a defect.**
  `SCALAR` / `FILE` / `RELATION_SINGLE` / `RELATION_MULTI` are plain `str` in
  `utils/inputs.py`, and CPython interns identifier-like string literals, so a redefinition
  spelling the *same* literal in `serializer_converter.py` would still be `is`-identical.
  What those four rows do catch is the deletion (an absent name fails through `_bound`) and
  a value drift, which is the regression shape that actually breaks the wire. Recorded here
  because a reader re-deriving the manifest will ask.
- **`_bound()` fails rather than errors on a missing name.** A bare `getattr` on a dropped
  symbol raises `AttributeError`, which reads in a summary like a collection problem rather
  than a ratchet verdict. Resolving through `vars(module)` with an explicit `pytest.fail`
  keeps a deletion — as much a DRY regression as a redefinition — inside the failure channel.
- **Two module-level tuples, not one tuple with a discriminator** (an explicit discretion
  item). The two tables are consumed by two different assertions (`is` versus
  `__code__ is`), so a discriminator would only be re-read to pick the assertion back apart.
  `ids=` is `<module tail>.<symbol>` (`inputs.pascalize_token`,
  `serializer_converter.SCALAR`), which is unique across all 20 rows and readable in a
  failure summary.
- **The package G2 row declares its schema inline**, as the ~20 other schema-declaring tests
  in that file do, rather than extracting an `_optimizer_schema(...)` helper for one call
  site. `_build_serializer_g2_schema` exists because the row needs Relay primaries plus a
  permissive `SerializerMutation` plus the optimizer extension, which is more setup than
  belongs inside a test body — but it is local to the row, and the plan's stated condition
  for extracting further (a second plan-shape row in this file) has not been met.
- **`ctx = SimpleNamespace(request=request)`, not a bare `SimpleNamespace()`.** The forms
  twin can pass a bare namespace; the serializer pipeline resolves a request through
  `request_from_info` on the way to `_merged_serializer_kwargs`, so the context has to carry
  one. The optimizer stashes `dst_optimizer_plan` on that same object either way.
- **The test module docstring was amended, not left alone.** It claimed "No ... G2 test is
  duplicated here"; after this slice the plan-state half of the G2 contract does live there.
  The docstring now names the split (behavioral half live, plan-object half package-internal)
  and the enumeration gained a matching bullet, so the file's own description of itself
  stays true.
- No process provenance anywhere in the diff: no severity label, no worker or round
  attribution, no slice number, in comments, docstrings, test names, or error strings.

### Notes for Worker 3

- **The two transiently-mutated files are pristine.** `optimizer/walker.py` and
  `rest_framework/inputs.py` were restored by `prove_failability.py` inside its own
  `finally`, the restore proved by byte comparison, and `git diff` over the pair is empty.
  Neither is in this slice's diff. The tool's own report is at
  `docs/builder/temp-tests/039-slice-3/proofs.md` and its manifest at
  `docs/builder/temp-tests/039-slice-3/proofs.json`, so an independent re-run is one command.
- **Re-run at the scopes recorded**, which differ per boundary (item 2 is
  `tests/rest_framework/test_resolvers.py`, item 1 adds the live products module, item 3 is
  the whole `tests/rest_framework/` directory). All three are inside the mandatory re-run
  floor at 3, 2, and 3 rows.
- **The full sweep is not green, and none of it is this slice.** Seven rows fail in the
  concurrent `spec-050` cycle's dirty files; the enumeration and the evidence are under
  `### Notes for Worker 1` item 3. The focused scope for this slice
  (`tests/rest_framework/` + `test_products_api.py`) is 631/631 green, and so is the floor run.
- **Unusual control flow worth a second look:** the live assertion selects the re-fetch by
  `[-1]` off `item_selects`. That ordering was read off a real run (see
  `### Implementation notes`), but it is positional, and a future change that adds a third
  real `products_item` `SELECT` after the re-fetch would silently re-point it. The mutation
  proof shows the row currently fails when the boundary is removed, which is the property
  that matters today.
- `scripts/review_inspect.py` was not re-run this pass; Worker 1's plan already recorded the
  overview for `rest_framework/resolvers.py`, and the production diff is six lines inside one
  existing function.
- **The new test file is untracked, so one gate has not actually run on it.** The
  `kanban-tracked-path-constants` hook reads `git ls-files`; an unstaged file is invisible to
  it. See `### Notes for Worker 1` item 5 — nothing to fix in the diff, but do not read that
  hook's green as coverage of `tests/rest_framework/test_dry_import_ratchet.py`.

### Notes for Worker 1 (spec reconciliation)

1. **Plan-vs-implementation drift, item 2: `meta` is still resolved through
   `getattr(mutation_cls, "_mutation_meta", None)`, not a direct read.** Small and
   mechanically obvious, implemented rather than paused, and surfaced here for your call.

   - Where it lives: `docs/builder/bld-039-slice-3-code_gaps.md`, `### Implementation steps`,
     the first bullet under step 1 (this artifact, not the spec).
   - Current wording: *"`meta = mutation_cls._mutation_meta` — a direct read, matching the
     four other `_mutation_meta` dereferences in this module (`:861`, `:1069`, `:1494`,
     `:2163`)."*
   - Recommended replacement: *"`meta = getattr(mutation_cls, "_mutation_meta", None)` —
     kept, so both incoherent spellings (the attribute absent, the attribute `None`)
     normalize into the one rejection below. The default no longer reaches a permit path, so
     it is not a fail-open shape; the two sibling defaults that did are retired."*
   - Why: a direct read makes the attribute-absent case an `AttributeError` and only the
     `None` case a `ConfigurationError`, which contradicts two other parts of the same plan
     that are operative rather than stylistic — the `### Test additions / updates` row
     *"`_mutation_meta` **attribute absent** now raises `ConfigurationError`"*, and the
     `#### Failability proofs` expectation *"Expected >= 3 rows (the three item-2 tests)"*
     for a `raise`->`return` mutation, which a direct read would hold to 2 because the
     absent-attribute row would still raise `AttributeError` with the boundary gone. It is
     also the shape `docs/builder/BUILD.md` `### Fail-open shapes` asks for: one guard on the
     ANSWER covering every spelling of the incoherent input, rather than a second guard per
     spelling. The measured proof records 3 rows, so the implemented shape is the one the
     plan's own acceptance condition needs.

2. **`tests/rest_framework/test_resolvers.py`'s module docstring now records the G2 tier
   split**, which is the same split note 4 of your plan asks Slice 2 to state in the spec.
   The file previously asserted *"No create/update happy path, envelope, reverse-map,
   partial-update, visibility, write-auth, authorize-before-decode, Upload, request-context,
   or G2 test is duplicated here"*; it now says `G2 BEHAVIORAL test` and carries a bullet
   naming the plan-object half. Whatever Slice 2 writes for the spec should agree with that
   wording, and the package path to cite is
   `tests/rest_framework/test_resolvers.py::test_serializer_refetch_keeps_select_related_suppresses_only`.

3. **Seven pre-existing test failures, escalated rather than acted on**
   (`docs/builder/BUILD.md` `## Claims are proven mechanically`: a failing test is not
   worker-verifiable, so the obligation is to record the evidence and escalate to the
   maintainer, who is the only party able to run a clean `HEAD` tree). `uv run pytest --no-cov`
   over all trees reports `7 failed, 7629 passed, 40 skipped`:

   - `tests/test_list_field.py::test_list_field_direct_call_schema_name_fallback_and_definition_lookup`
   - `tests/test_list_field.py::test_list_field_post_orderset_validator_arms`
   - `tests/test_list_field.py::test_list_field_constructor_validation_precedence`
   - `tests/test_list_field.py::test_list_arguments_immutability_and_slots`
   - `tests/utils/test_querysets.py::test_validate_post_orderset_result_routing_hints_none_vs_empty`
   - `tests/orders/test_sets.py::test_input_has_active_terms_hostile_eq_and_repr`
   - `examples/fakeshop/test_query/test_list_field_api.py::test_holder_materialized_and_nullable_none_fields`

   Evidence that none belongs to this slice: three of the four owning test files
   (`tests/test_list_field.py`, `tests/utils/test_querysets.py`, `tests/orders/test_sets.py`)
   are named verbatim in this plan's baseline-dirty paragraph as the concurrent `spec-050`
   cycle's files; the fourth exercises `django_strawberry_framework/list_field.py`, which is
   dirty from the same cycle and appears in the traceback
   (`list_field.py::_handle_non_queryset_rejections_sync` raising `ListArgumentError` for
   `orderBy` on `branchesMaterialized`). No file in this slice's diff appears in any of the
   seven tracebacks, and this slice's own focused scope plus the floor run are green. No
   action taken, no file touched.

4. **Not a spec issue, recorded for the manifest's next reader.** The 20 rows in
   `tests/rest_framework/test_dry_import_ratchet.py` were re-measured at `HEAD` in this pass
   before the file was written — every row printed `identical=True` from a real import under
   `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop`, matching your plan's
   measured tables exactly. Neither the dispatch's six-symbol list nor the spec's
   `### Import manifest` was used. The four kind-constant rows carry the interning ceiling
   described in `### Implementation notes`; if Slice 2 restates the DoD check's mechanism
   (your note 2), saying it pins *identity* is accurate, and saying it would catch a
   same-valued re-spelling of a `str` constant would not be.

5. **A new tracked test file means `examples/fakeshop/apps/kanban/constants.py` goes stale at
   staging time, and that file is outside this slice's writable set.**
   `tests/rest_framework/test_dry_import_ratchet.py` is new; `apps/kanban/constants.py`
   currently lists five `tests/rest_framework/` files and not this one (verified by grep).
   The `kanban-tracked-path-constants` pre-commit hook rewrites that module from
   `git ls-files`, so it sees the new file only once it is STAGED — `uvx pre-commit run
   --files <the four owned files>` passed here precisely because the file is still untracked,
   which is `START.md`'s documented fail-open for that hook. Left untouched deliberately: the
   maintainer-set fence for this cycle names spec files and this slice's four `.py` files, and
   `constants.py` is neither. The remedy at commit time is `uv run python
   scripts/build_kanban_tracked_path_constants.py` after `git add`, landed as a
   constants-only sync commit (the hook's `files:` pattern does not match that module, so it
   cannot roll itself back). Recorded so it reaches the integration pass rather than surfacing
   as a hook rollback on the maintainer's first commit.

---

## Review (Worker 3)

### Independent failability re-run — mutations recorded BEFORE they are applied

All three of Worker 2's recorded boundaries fail 3 / 2 / 3 rows, so **every one of them
is inside `docs/builder/worker-3.md`'s mandatory re-run floor (3 or fewer)**. The re-run
subset is therefore all three; nothing is accepted on Worker 2's record alone. Recorded
here before any mutation is applied, per `docs/builder/worker-3.md` `## Scope`.

Instrument: `uv run python scripts/prove_failability.py` over a Worker-3-owned manifest at
`docs/builder/temp-tests/039-slice-3/w3-proofs.json`, `--scratch-root` under the session
scratchpad (**outside the repository**), `--output docs/builder/temp-tests/039-slice-3/w3-proofs.md`.
Each mutation is applied and reverted one at a time by the tool, in the fenced-loop order,
with the anchor check first and the restore proved by byte comparison.

1. `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` —
   replace the whole no-validated-snapshot `raise ConfigurationError(...)` with `return`,
   i.e. put the retired fail-open back. Scope as Worker 2 recorded it:
   `tests/rest_framework/test_resolvers.py`.
2. `django_strawberry_framework/optimizer/walker.py::_enable_only_for_operation` — replace
   `    return operation is None or operation is OperationType.QUERY` with `    return True`,
   re-enabling `.only(...)` under a MUTATION. Scope as recorded:
   `tests/rest_framework/test_resolvers.py examples/fakeshop/test_query/test_products_api.py`.
3. `django_strawberry_framework/rest_framework/inputs.py::_serializer_shape_build_cache` —
   after the module tail, re-bind `pascalize_token`, `make_input_namespace`, and
   `make_shape_build_cache` to same-named local delegating wrappers. Scope as recorded:
   `tests/rest_framework/`.

Neither `optimizer/walker.py` nor `rest_framework/inputs.py` is in this slice's diff;
both were confirmed byte-clean against `HEAD` (`git diff --stat` over the pair prints
nothing) **before** this re-run began, which is what proves no prior mutation was still
live when the anchors were read.

**Pre-record provenance.** The three-entry block above was written by an interrupted
Worker 3 pass that produced `docs/builder/temp-tests/039-slice-3/w3-proofs.json` / `.md`
but never wrote a verdict into this artifact. This pass adopts it as the required
before-the-mutation record, re-verified its precondition independently, and re-ran all
three boundaries itself under its own manifest
(`docs/builder/temp-tests/039-slice-3/w3-pass2-proofs.json`, output
`.../w3-pass2-proofs.md`). Precondition re-verified before any mutation:
`git diff --stat` over `django_strawberry_framework/optimizer/walker.py` and
`django_strawberry_framework/rest_framework/inputs.py` prints nothing (both byte-clean vs
`HEAD`), no `ACTIVE-MUTATION.json` marker exists anywhere under the repo or the scratch
root, and `--check-anchors-only` reported all three anchors matching **exactly once** —
which is what proves no prior mutation was live when the anchors were read.

### Independent re-run result — node-id SETS, at Worker 2's recorded scopes

Instrument: `uv run python scripts/prove_failability.py
docs/builder/temp-tests/039-slice-3/w3-pass2-proofs.json --scratch-root <session
scratchpad>/w3-failability --output docs/builder/temp-tests/039-slice-3/w3-pass2-proofs.md`,
**exit code 0**. All three boundaries fall at or under the mandatory re-run floor (3 / 2 /
3 rows), so the re-run subset is **all three**; **nothing is accepted on Worker 2's record
alone.** Every scope below is the scope Worker 2 recorded, unwidened.

1. `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` —
   scope `tests/rest_framework/test_resolvers.py`; pre-mutation `172 passed`, exit 0, 0
   pre-existing failures; collection/setup errors **0**; failing set (3):
   - `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_missing_mutation_meta_snapshot`
   - `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_none_mutation_meta_snapshot`
   - `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_a_missing_snapshot_on_the_annotation_axis`
2. `django_strawberry_framework/optimizer/walker.py::_enable_only_for_operation` — scope
   `tests/rest_framework/test_resolvers.py examples/fakeshop/test_query/test_products_api.py`;
   pre-mutation `307 passed`, exit 0, 0 pre-existing failures; collection/setup errors
   **0**; failing set (2):
   - `tests/rest_framework/test_resolvers.py::test_serializer_refetch_keeps_select_related_suppresses_only`
   - `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`
3. `django_strawberry_framework/rest_framework/inputs.py::_serializer_shape_build_cache` —
   scope `tests/rest_framework/`; pre-mutation `496 passed`, exit 0, 0 pre-existing
   failures; collection/setup errors **0**; failing set (3):
   - `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_input_namespace]`
   - `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_shape_build_cache]`
   - `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.pascalize_token]`

**Every node-id set is byte-identical to Worker 2's**, at identical scope, with identical
pre-mutation baselines and zero collection/setup errors on both sides. The restore SHA-256
prefixes this pass measured (`384ea9a0bd4731ba`, `102a71658c211aa8`, `c97f01100b3bd840`)
also match Worker 2's, which independently corroborates that both passes mutated and
restored the same pristine bytes. Post-run, `git diff --stat` over `walker.py` and
`inputs.py` prints nothing and no marker file exists; `resolvers.py` carries only the
slice's own 14/3 change.

Boundary 2 sits at 2 rows — above the weakly-pinned 0-or-1 threshold, and both halves of
item 1 (package plan row, live SQL row) are in the failing set, which is the plan's stated
closure condition for that item.

### Two mutations audited as boundary-removing, not boundary-perturbing

- Boundary 2's mutation is `_enable_only_for_operation` -> `return True`. Read against
  `django_strawberry_framework/optimizer/walker.py:121-165`, that gate is derived **once**
  per walk and threaded as a single `enable_only` bool through every recursion, so forcing
  it true reinstates `.only(...)` across the whole plan tree under a MUTATION. It removes
  exactly the property both item-1 assertions claim.
- Boundary 3's mutation appends same-named delegating re-bindings **after** the module
  tail, past every call site, so runtime behavior is unchanged and only identity moves —
  and the run shows three ratchet rows failing with **no collateral failure**, which is the
  evidence the wrapper was behavior-preserving rather than a broad breakage that would have
  inflated the count.

### High:

None.

### Medium:

None.

### Low:

None.

### Verdict on Worker 2's plan-drift call (item 2)

**The drift call is correct and the shipped shape is the better one.** Worker 2 kept
`meta = getattr(mutation_cls, "_mutation_meta", None)` and made its `None` arm raise,
against the plan's prescribed direct attribute read
(`django_strawberry_framework/rest_framework/resolvers.py:1169-1181`).

`docs/builder/BUILD.md` `### Fail-open shapes` asks for a guard on the **answer**, not on
one spelling of the incoherent input. The answer this tail computes is "do the runtime
field's requiredness and annotation agree with the schema's?", and it is undeterminable
under **both** incoherent spellings — the attribute absent, and the attribute present but
`None` (the abstract-base case). The shipped shape funnels both into one
`ConfigurationError`; the plan's direct read would have split them, leaving the absent case
as a bare `AttributeError` — a different exception type, a different message, and not the
framework's own boundary. That is precisely the "guard written against an input spelling"
the section rejects, so the plan's own prescription was the weaker of the two here. The
`getattr` default that survives is no longer a fail-open shape because its default no
longer reaches a permit path; it reaches the raise.

The two sibling defaults **did** go with it: `getattr(meta, "operation", "create")` and
`getattr(meta, "optional_fields", None)` are now `meta.operation` and
`meta.optional_fields` (`:1183-1184`). Fixing one spelling and leaving two — the failure
mode the dispatch named — did not happen. Verified safe against the real snapshot:
`django_strawberry_framework/mutations/sets.py::_ValidatedMutationMeta` declares both
`operation` and `optional_fields` in `__slots__` and assigns both unconditionally in
`__init__`, so no bound mutation can reach the tail without them. `frozenset(... or ())` is
correctly kept: `optional_fields` is `tuple[str, ...] | None` and `None` and `()` are the
same answer there, so it was never the fail-open — the `getattr` around it was.

**Reachability of the sibling change was checked, not assumed.** The only production caller
of the guard is `rest_framework/resolvers.py:2269` inside the serializer write step, where
`meta` is always a real `_ValidatedMutationMeta`. The one other duck-typed `_mutation_meta`
shape in the package, `auth/mutations.py::_AuthMutationMetaSnapshot`, carries `operation`
but **no** `optional_fields` — it would now raise `AttributeError` at `:1184` where the old
`getattr` tolerated it. It cannot reach this code: an auth holder is not a
`SerializerMutation` and never enters `_guarded_serializer_write`. Recorded because it is
the one way the sibling retirement could have bitten.

### Test-staleness sweep, run independently of the slice's file list

Retiring `getattr(meta, "optional_fields", None)` makes that attribute **mandatory** on any
duck-typed meta that reaches the tail, which is exactly the class
`docs/builder/BUILD.md` `### Test staleness a focused run cannot see` describes: a
stranded fixture in a tree the diff never names. Swept all three test trees for
`SimpleNamespace(operation=` and for `_mutation_meta` assignments — population 15 and 31
respectively, both printed, not counted blind.

- Three fakes at `tests/rest_framework/test_resolvers.py:3784`, `:3811`, `:3851` build
  `_mutation_meta=SimpleNamespace(operation=...)` with **no** `optional_fields`. Read in
  full: all three call `_assert_runtime_write_source_ownership`, never the agreement guard,
  so none reaches the tail. Not stale.
- Every other hit is in `tests/mutations/`, `tests/optimizer/`, `tests/forms/`,
  `tests/auth/`, `tests/test_schema.py` and touches unrelated call sites.
- `examples/` contributes zero hits.

The three fakes Worker 2 **did** amend (`:1432`, `:1447`, `:1477`) are the complete
population that reaches the tail, and each still pins what it pinned before — the fix
restores the tests' intent against the current contract rather than weakening an assertion.

### The concurrent cycle's seven failures — obligation discharged, no re-derivation

`docs/builder/BUILD.md` `## Claims are proven mechanically` makes a runtime
"pre-existing at HEAD" claim not worker-verifiable in a dirty tree, so the only obligation
here is that no traceback names a file in this diff. Reproduced the seven at a scope
containing **none** of this slice's four files:
`uv run pytest tests/test_list_field.py tests/utils/test_querysets.py tests/orders/test_sets.py
examples/fakeshop/test_query/test_list_field_api.py --no-cov -q` -> `7 failed, 530 passed`,
the same seven node ids Worker 2 listed. Read the tracebacks: all are `spec-050` surface
drift — a `ConfigurationError` message reworded (`"must be a positive integer, got -1."` ->
`"must be a positive integer; got int -1."`), a `_ListArguments` frozen-dataclass
`__setattr__` `TypeError`, and an `apply_sync` result-cache message. **No file in this
slice's diff appears in any of the seven tracebacks.** Escalated to the maintainer as the
only party who can run a clean `HEAD` tree; nothing acted on, nothing touched.

### Hot-path budget — verified to exist and be reproducible as recorded

The obligation is that the number exists and reproduces, never that it is good
(`docs/builder/BUILD.md` `## Hot-path budget`). Re-ran Worker 2's driver unchanged:
`uv run python docs/builder/temp-tests/039-slice-3/hotpath.py` -> `MEDIAN per-call:
0.464 us`, against Worker 2's recorded post-edit **0.467 us** and its stated unchanged-code
spread of **0.028 us**. Reproducible within its own declared noise band. Metric 2 was
re-read off the diff rather than the prose: 3 defaulted `getattr` calls became 1 `getattr`
plus 2 direct reads, total attribute accesses per field unchanged at 3. Both figures
recorded rather than one, so the maintainer sees the spread. **Whether the trade is
acceptable is the maintainer's call, not this review's.**

### Floor verification — confirmed it happened as recorded

Every element of the plan's declaration checked against the artefacts on disk, not the
prose:

- Scratch venv exists at the recorded path, **outside the repository**.
- `uv pip list --python <venv>/bin/python` reads back exactly what the build report
  recorded: CPython **3.10.19**, `django` **5.2.16**, `strawberry-graphql` **0.316.0**,
  `django-filter` 26.1, `pytest` 9.1.1, `pytest-django` 4.14.0 — matching
  `docs/builder/BUILD.md` `## Floor verification`'s canonical floor.
- `djangorestframework` **3.18.0** is present. This was the load-bearing check: absent, every
  `rest_framework` module would skip and the run would prove nothing.
- Shared `.venv` **unmutated** — still Django 6.1 / strawberry-graphql 0.324.0, so no
  concurrent session's floor was silently moved.
- Re-ran the declared focused scope at the floor:
  `<venv>/bin/python -m pytest -n0 --no-cov -q tests/rest_framework/test_resolvers.py
  tests/rest_framework/test_dry_import_ratchet.py
  "examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count"`
  -> **`193 passed`**, the exact count recorded. The version-sensitive reason the plan
  scoped this run — the live row's SQL column-text assertion — holds at the floor.

### Item 1: the replacement assertion distinguishes in both directions

- **Direction "boundary gone":** the walker mutation makes both halves fail (re-run set
  above). The retired line could not have — it queried
  `models.Item.objects.values_list("name", flat=True)` afresh and never read `captured`.
- **Direction "boundary holds":** both halves pass green in every unmutated baseline (307,
  193 at the floor, 496).
- The anchor is five columns (`description`, `attachment`, `is_private`, `created_date`,
  `updated_date`), every one outside what a `.only(...)` projection for
  `node { name category { name } }` could carry, so it is not satisfiable by a projected
  row.
- **Worker 2's own flagged fragility is already fenced.** The row selects the re-fetch
  positionally as `item_selects[-1]`, and Worker 2 warned a future third real
  `products_item` `SELECT` would silently re-point it. It would not: the
  `assert len([... "select 1" not in s ...]) == 2, sql` assertion sits immediately above and
  fails first. Recorded rather than filed, because the guard already exists.
- **The two absolute count assertions beside it survived untouched**, as did
  `len(captured) == 17` — the diff hunk touches only the final assertion block. Those are
  the batching pin and were derived from a real run.
- **Nothing was lost by deleting the old line.** `result["node"] == {"name": "SerG2Widget",
  "category": {"name": category.name}}` above it already proves the row was written and
  reads back.

### Tier placement — both halves checked against the coverage rule, in both directions

`examples/fakeshop/test_query/README.md` #"Coverage rule." and `AGENTS.md` place a line
reachable from a real query in the live tier.

- **The live half is genuinely reachable:** it drives a real `/graphql/` POST through
  `django.test.Client` under `CaptureQueriesContext` and asserts on emitted SQL text.
- **The package half genuinely is not:** it asserts `ctx.dst_optimizer_plan`, the
  optimizer's last-wins stash on the context object. No HTTP response carries it, so the
  live tier structurally cannot express the assertion. The `select_related == ("category",)`
  half is load-bearing, not decoration — because the stash is last-wins, it is what proves
  the captured plan IS the re-fetch plan.
- The split mirrors the shipped precedent
  `tests/forms/test_resolvers.py::test_modelform_refetch_keeps_select_related_and_suppresses_only`
  (`tests/forms/test_resolvers.py:2131`), confirmed present.
- The two halves assert **different** properties, so the file does not end up with two live
  G2 assertions and the package row is not a stand-in duplicating a live-earned verdict.
- The cross-tier pointer in the live comment resolves: `check_citations.py --check` reports
  `OK: 963 citations resolve`, which includes the new
  `tests/rest_framework/test_resolvers.py::test_serializer_refetch_keeps_select_related_suppresses_only`
  citation.

### Item 3: shape and manifest provenance both verified independently

- **Parametrized, not looped.** Two `@pytest.mark.parametrize`d functions over two
  module-level tuples: **20 node ids** (18 + 2), confirmed by the ids appearing individually
  in the failing set. `START.md` `## Instruments that lie` — a `for` loop inside one test
  caps failability at 1 — does not apply.
- **Built from measured imports at HEAD, not from the spec or the plan.** Re-derived the
  population independently: imported both consumer modules under
  `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop` and enumerated every
  name whose bound object is identical to a same-named object in `utils/inputs.py`,
  `utils/converters.py`, or `utils/strings.py`. **All 18 manifest rows resolve to a genuinely
  identical binding; the set of manifest rows that are NOT identical is empty.** None of the
  stale spellings the audits caught (`build_and_stash_input`, `reject_unknown_meta_keys`,
  `visible_related_object`, `_normalize_field_sequence`, `_pascalize_token`) appears — the
  manifest uses the live spellings, so it does not `AttributeError` on correct code.
- **`_bound()` fails rather than errors on a deletion**, keeping a dropped symbol inside the
  failure channel instead of surfacing as something a summary reads as a collection problem.
  Deletion is as much a DRY regression as redefinition, and this is the arm that catches it.
- The four kind-constant rows carry a real ceiling (interned `str` literals make a
  same-valued re-spelling `is`-identical). Worker 2 disclosed it in
  `### Implementation notes` and routed the consequence to Worker 1 so the spec's DoD
  restatement cannot overstate it. Correct handling; those rows still catch deletion and
  value drift.

### DRY findings

- **No new duplication introduced by the slice.** Item 1's two halves assert different
  properties, item 3 puts one manifest in one file covering both consumer modules rather
  than splitting it across `test_converter.py` and `test_inputs.py`, item 4 reuses its
  rejection twin's scaffolding and differs in one expression, and item 2 added no helper.
- **`_build_serializer_g2_schema` is correctly not extracted further.** The file already
  carries **10** inline `class CategoryT(DjangoType` declarations, 12 `DjangoSchema(` calls
  and 14 `finalize_django_types()` calls — declaring a schema inline is this file's
  established idiom, and the slice adds two more to a pre-existing ten. Consolidating is a
  whole-file refactor that belongs to its own card, not to a four-item review round.
  Recorded as a standing candidate, not held.
- **The ratchet's population is narrower than the measured shared substrate.** The census
  above found **10 further** bindings in the two consumer modules that are already
  object-identical to their `utils/` owners and are outside `SHARED_BINDINGS`:
  `inputs.optional_input_field`, `inputs.resolve_effective_fields`,
  `inputs.guard_dropped_required`, `inputs.iter_input_field_collisions`,
  `inputs.generated_input_type_name`, `inputs._safe_arg_repr`,
  `serializer_converter.FieldConversionBase`, `serializer_converter.pascal_case`,
  `serializer_converter._safe_type_name`, `serializer_converter._safe_arg_repr`. **Not a
  finding:** the shipped manifest is exactly the population the spec's `**DRY / reuse**`
  bullet enumerates (P1.3 / P1.4 / P2.1 / P2.2 / P2.3 plus the kind enum and the two string
  helpers), and the module docstring scopes itself honestly — "the manifest is the
  population this guard covers". Widening it is a **spec-scope** question, routed to Worker 1
  below rather than decided here.
- **No existence challenge raised.** Item 3's manifest is the one new abstraction and it has
  two real consumers (both parametrizations) with no indirection over anything; item 2 added
  no helper, and the plan's reasoning for not extracting a one-call-site
  `_require_mutation_meta` accessor over an attribute read on the request path is sound.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the
re-export list are unchanged; the slice adds no public export. No spec authorization needed.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The diff is four
`.py` files. The `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` modification present in
the tree is **this cycle's Slice 0 rationale extraction**, not `spec-050` and not this slice
— attributed by diff content (729 deletions moving the inline revision history out to the
untracked `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` companion).
Recorded so the record is accurate; out of scope here either way.

### Gate re-verification

Re-ran the gates on the four owned files rather than accepting the build report's pass/fail:
`ruff format --check` -> `4 files already formatted`; `ruff check` -> `All checks passed!`;
`scripts/check_trailing_commas.py --check` -> exit **0**; `scripts/check_citations.py
--check` -> `OK: 963 citations resolve`. The new test file is ASCII-clean.

### What looks solid

- The item-2 boundary is the right shape and the right severity of loud: one rejection
  covering every incoherent spelling, sited on the answer, with the two sibling defaults
  retired alongside it rather than left as the half-fix the dispatch warned about.
- Three item-2 rows rather than one, deliberately spanning both incoherent spellings **and**
  the annotation axis, so the boundary is not resting on a single assertion.
- Both item-1 halves appear in the walker mutant's failing set. That is the strongest
  available evidence that the finding was **closed** rather than relocated: the previous
  line could not have appeared there at all.
- The ratchet is parametrized, HEAD-measured, honest about its own ceiling, and its
  deletion arm routes through `pytest.fail` rather than an `AttributeError` that would read
  as a collection problem.
- The item-4 tolerance arm genuinely exercises the tolerated branch: traced
  `rest_framework/resolvers.py::_merged_serializer_kwargs` #"if override_request is not None and override_request is not request:"
  — the hook's echoed object makes the first conjunct true and the identity test false, so
  the arm is reached rather than short-circuited by an earlier guard.
- Worker 2's build report flags its own weak points (the positional `[-1]`, the interning
  ceiling, the untracked-file hook fail-open) instead of leaving them for the reviewer, and
  each one held up under checking.
- The floor run was real, at the declared floor, with the soft dependency confirmed present
  **before** the result was read.

### Temp test verification

- No temp **tests** were written; every review suspicion was answerable by reading, by an
  independent census, or by the failability re-run.
- Files created under `docs/builder/temp-tests/039-slice-3/` by this pass:
  `w3-pass2-proofs.json` (this pass's own copy of the proof manifest) and
  `w3-pass2-proofs.md` (its measured report). **Disposition: kept** as the on-disk evidence
  for the independent re-run recorded above; the directory is gitignored and is cleared per
  cycle by `scripts/clean_up.py`. Nothing under it is the sole proof of shipped behavior —
  every boundary is pinned by permanent rows.
- The earlier interrupted pass's `w3-proofs.json` / `w3-proofs.md` were read for provenance
  and left in place; they differ from Worker 2's report only in run timings.
- `scripts/review_inspect.py` was **not** run this pass. Reason recorded per
  `docs/builder/worker-3.md` `## Static helper use`: the production diff is 14 lines inside
  one existing function of a file Worker 1 already ran the helper over at plan time, and the
  repeated-literal evidence the DRY findings needed came from an executable identity census
  (a stronger instrument than a literal scan) plus a direct count of the file's inline-schema
  idiom.

### Notes for Worker 1 (spec reconciliation)

Worker 2's five notes are all accurate as written and are not restated here. Additions:

1. **Escalated — the DoD check's population, not just its mechanism.** Worker 2's note 2
   already asks Slice 2 to restate the `**DRY / reuse**` bullet's "grep guard" as an identity
   guard. Slice 2 should also settle the **population**, because the census in this review
   found 10 further bindings already object-identical to their `utils/` owners and outside
   the shipped manifest (enumerated under `### DRY findings`). Two resolution paths, both
   legitimate, and the choice is a spec-scope call rather than a worker's: **(a)** restate
   the DoD as covering the spec's *named promotions* (P1.3 / P1.4 / P2.1 / P2.2 / P2.3 plus
   the kind enum and the string helpers), which is exactly what shipped and makes the current
   manifest complete by definition; or **(b)** define the DoD as the *whole* shared-substrate
   surface, which makes the manifest under-populated by 10 rows and owes a follow-up. Nothing
   in the shipped code is wrong under either reading — the module docstring already scopes
   itself to "the population this guard covers".
2. **The sibling `getattr` retirement narrowed the tolerated meta shapes, and that is worth
   one spec sentence.** After this slice, any object reaching `_assert_field_agreement`'s
   tail must carry `operation` **and** `optional_fields`. `_ValidatedMutationMeta` always
   does; `auth/mutations.py::_AuthMutationMetaSnapshot` does **not**, and is unreachable from
   this call site today. Whatever Slice 2 writes for rev6 #1 should state the snapshot
   requirement as a contract, so a future flavor that reuses the auth-style duck-typed
   snapshot cannot reach this tail unnoticed.
3. **Escalated (standing, not this slice's) — the inline-schema idiom in
   `tests/rest_framework/test_resolvers.py`.** 10 inline `CategoryT` / `ItemT` declarations,
   12 `DjangoSchema(` calls, 14 `finalize_django_types()` calls. The slice correctly followed
   the idiom rather than fighting it, but the idiom itself is a consolidation candidate that
   wants its own card. Resolution paths: leave as-is (it is a test file where explicit
   local declaration aids readability), or extract a parametrizable schema builder in a
   dedicated cleanup card. Not held.
4. **Worker 2's note 5 is confirmed by measurement, not accepted on prose.**
   `examples/fakeshop/apps/kanban/constants.py:242-247` lists six `tests/rest_framework/`
   paths and not `test_dry_import_ratchet.py`. The `kanban-tracked-path-constants` hook reads
   `git ls-files`, so it cannot see an untracked file — the green `uvx pre-commit` run is
   `START.md`'s documented fail-open for that hook, not coverage of the new file. The remedy
   Worker 2 records (regenerate after `git add`, land as a constants-only sync commit) is the
   correct one and must reach the integration pass or the maintainer's first commit rolls
   back.
5. **Worker 2's note 7 in the plan section stands.** The build plan on disk still carries
   none of the three sections the dispatch names. That is Worker 0's to land before the
   integration pass; this review confirms it is still absent.

### Review outcome

`review-accepted`. All four dispatched findings are closed by the diff, each with a fix that
**refuses an input previously accepted** rather than relabelling a detection: item 2 now
rejects a mutation reaching the agreement tail with no validated snapshot (both spellings),
item 1's assertions now fail when the G2 gate is removed and previously could not, item 3's
ratchet now fails on a same-named local redefinition and on a deletion, and item 4 now pins
the tolerated arm that had no row. Every boundary was inside the mandatory re-run floor and
**every one was re-run independently at Worker 2's recorded scope**, with node-id sets
matching exactly and zero collection or setup errors on both sides. No boundary is weakly
pinned; no zero-row entry exists, so no **why 0** judgement is owed. No High, Medium, or Low
findings. The hot-path number exists and reproduces within its declared noise band, the
floor run is confirmed real at the canonical floor with the soft dependency present, the
public surface is unchanged, and the seven full-sweep failures reproduce at a scope
containing none of this slice's files with no traceback naming any of them — recorded and
escalated to the maintainer, not re-derived. The two spec-scope questions above are routed
to Worker 1 with an `Escalated:` framing and resolution paths; neither blocks the slice.


---

## Final verification (Worker 1)

**Outcome: `revision-needed`.** One box over-ticked: the DRY import ratchet omits a
promotion the spec's own DoD sentence names. Everything else in the slice holds, including
both escalations, which are decided below.

### Dispatched findings checklist — audit, box by box

Each box audited against the working-tree diff (`git diff -- <the four owned files>` plus
the untracked new test file), never against the build report's prose.

1. **High — the G2 "no `.only(...)`" claim has no distinguishing assertion. `- [x]` STANDS.**
   Both halves are in the diff. Live:
   `examples/fakeshop/test_query/test_products_api.py` now takes
   `refetch_select = [s for s in item_selects if "select 1" not in s.lower()][-1]` and
   asserts five `"products_item"."<column>"` names against it — `description`,
   `attachment`, `is_private`, `created_date`, `updated_date` — every one outside the
   `id` / `name` / `category_id` a `.only(...)` projection for `node { name category { name } }`
   could carry, read off the already-captured SQL with no fresh query. The retired line
   (`assert "SerG2Widget" in models.Item.objects.values_list("name", flat=True)`) is gone,
   not supplemented. Package:
   `tests/rest_framework/test_resolvers.py::test_serializer_refetch_keeps_select_related_suppresses_only`
   asserts `plan.select_related == ("category",)` **and** `plan.only_fields == ()` off
   `ctx.dst_optimizer_plan`. The box's stated closure condition — both halves in the
   walker mutant's failing set — is met and was measured twice independently.
2. **Medium — a fail-open guard. `- [x]` STANDS.**
   `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`:
   `if meta is None:` now raises `ConfigurationError` instead of returning, and the two
   sibling defaults on the same four lines are gone —
   `getattr(meta, "operation", "create")` → `meta.operation`,
   `frozenset(getattr(meta, "optional_fields", None) or ())` →
   `frozenset(meta.optional_fields or ())`. Three rejection rows landed
   (`::test_agreement_guard_rejects_a_missing_mutation_meta_snapshot`,
   `::test_agreement_guard_rejects_a_none_mutation_meta_snapshot`,
   `::test_agreement_guard_rejects_a_missing_snapshot_on_the_annotation_axis`), and the
   three pre-existing `_agreement_specs_with_meta` fakes that reach the tail gained
   `optional_fields=()` rather than having an assertion weakened.
3. **Medium — the DRY import ratchet was never written. `- [x]` UN-TICKED — over-tick.**
   The file, the shape, and the failability proof are all correct; the **population is
   short by one row against the spec's own named promotions.** The DoD sentence
   (`## Slice checklist` → Slice 1 → `**DRY / reuse**`, spec `:640-642`) makes the check
   cover "these", whose antecedent is the five promotions enumerated in the same sentence.
   **P2.1 names two shapes, not one:** `### Cross-flavor reuse and DRY obligations`
   `- **P2.1 — unify the field-spec / conversion types.**` (spec `:2466-2474`) closes
   *"Unify the conversion result (`annotation` + `kind` + `required`) into one shared shape
   too."*, and the `### Import manifest` row for `serializer_converter.py` (spec `:2582`)
   names it again as "the unified **conversion / field-spec** dataclass (**P2.1**)". That
   shape shipped as `django_strawberry_framework/utils/inputs.py::FieldConversionBase`,
   subclassed by both flavors (`forms/converter.py::FormFieldConversion`,
   `rest_framework/serializer_converter.py::SerializerFieldConversion`) and imported by
   `serializer_converter.py`. Measured at `HEAD` under
   `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop`:
   `vars(serializer_converter)["FieldConversionBase"] is utils_inputs.FieldConversionBase`
   → `True`. It is **absent from `SHARED_BINDINGS`**, so a local redefinition of the
   conversion base in `serializer_converter.py` — a body copy that behaves identically and
   therefore breaks no behavioral row — is invisible to every test in the tree. That is the
   exact regression class the ratchet exists to catch, on the exact symbol the spec
   promoted. Audit 1a already recorded the population: its **D2** row grades P2.1
   BUILT-CONFORMANT citing `utils/inputs.py::InputFieldSpec` **and** `::FieldConversionBase`,
   and its **F1** row lists the real imports as
   `utils/inputs.py::{FieldConversionBase, InputFieldSpec, SCALAR, RELATION_SINGLE, RELATION_MULTI, FILE}`
   — the shipped manifest took five of those six.
   **Remaining work, and it is one line:** add
   `(serializer_converter, "FieldConversionBase", utils_inputs),` to `SHARED_BINDINGS` in
   `tests/rest_framework/test_dry_import_ratchet.py` (19 identity rows, 21 node ids). The
   existing failability proof's manifest and scope are unaffected; re-run it so the
   recorded node-id set matches the shipped file. No production change, no spec change.
   This row is in **every** candidate population (see `### Escalation A` below), so adding
   it now cannot be invalidated by the maintainer decision routed there.
4. **Low — the request-identity guard's tolerance arm is unpinned. `- [x]` STANDS.**
   `tests/rest_framework/test_resolvers.py::test_merged_kwargs_override_echoing_the_same_request_object_is_tolerated`
   returns `kwargs["context"] = {"request": info.context.request}` from the hook and
   asserts no raise plus `kwargs["context"]["request"] is request`. Traced against
   `rest_framework/resolvers.py::_merged_serializer_kwargs`
   #"if override_request is not None and override_request is not request:" — the echoed
   object makes the first conjunct true and the identity test false, so the tolerated arm
   is genuinely reached rather than short-circuited earlier.

No box is left `- [ ]` undeferred: box 3 is un-ticked with the remaining work named above,
which is a re-loop rather than a deferral.

### Escalation A — which population the DoD ratchet should hold

**Decision: the spec's NAMED promotions, and the answer changes the shipped test.**

- **This half is mine to decide, not the maintainer's.** It is a reading of an existing
  contract — what "these" refers to in the spec's own DoD sentence — not a choice about
  which contract the package should offer. `docs/builder/BUILD.md`
  `### Contract-level findings are escalated as maintainer decisions before dispatch`
  distinguishes the two; this is the first kind.
- **The reading:** "these" = the promotions enumerated in the same bullet — P1.4 (the
  converter dispatch skeleton), P2.1 (the unified field-spec **and** conversion shapes),
  P2.2 (the one-ledger input-namespace trio), P1.3 (the shape-build cache), P2.3 (the
  divergent-shape suffix helper). The shipped manifest covers P1.4 (4 rows), P1.3 (2 rows),
  P2.2 (1 row + both Table B `__code__` rows), P2.3 (1 row), and P2.1's field-spec half
  (2 rows) — but not P2.1's conversion half. Hence box 3's un-tick.
- **The shipped manifest's non-promotion rows are correct to keep.** The four input-kind
  constants and the two `graphql_camel_name` rows are not P-labelled promotions, but
  `rest_framework/serializer_converter.py` states the single-sourcing contract in shipped
  source (#"single-sourced in ``utils/inputs.py`` (one conceptual enum,") and the
  `### Import manifest` names `graphql_camel_name` in both module rows. Covering a contract
  the shipped source itself asserts is not scope creep.
- **Worker 3's census framing does not survive re-derivation, in two ways.** Its
  `### DRY findings` says the shipped manifest "is exactly the population the spec's
  `**DRY / reuse**` bullet enumerates". It is not — it is that population minus
  `FieldConversionBase`. And the census's own "**10 further** bindings" is a figure of its
  instrument, not of the population: it compared only against `utils/inputs.py`,
  `utils/converters.py`, and `utils/strings.py`. Re-measured at `HEAD` against every owner
  the `### Import manifest` names, `serializer_converter.py` also binds
  `types/converters.py::{convert_scalar, scalar_for_field}` and `exceptions::ConfigurationError`
  identically. So "10" understates its own option-(b) population. **Publish no figure from
  that glob** (`START.md` `## Instruments that lie`, positive-vocabulary census).
- **Widening the ratchet to the whole shared substrate IS a maintainer decision, and I do
  not make it.** It would create a standing obligation the spec never wrote — every future
  import into either module becomes a manifest row or a silent hole — and the cost lands on
  work that has nothing to do with `spec-039`. Alternatives, each with what it loses:
  - **(a) Named promotions only** (this slice's shape, plus the missing row). *Loses:* a
    redefinition of a shared symbol the spec never promoted — `pascal_case`,
    `optional_input_field`, `resolve_effective_fields`, `guard_dropped_required`,
    `iter_input_field_collisions`, `generated_input_type_name`, `convert_scalar`,
    `scalar_for_field` — goes uncaught. *Gains:* the manifest stays auditable against a
    written contract, and completeness is decidable by reading the spec.
  - **(b) The whole measured shared substrate.** *Loses:* the manifest becomes a census
    with no written source of truth, so "is it complete?" is answerable only by re-running
    the census — and it goes stale on every legitimate new import, which is a maintenance
    tax paid by unrelated cards. *Gains:* no shared binding can be silently forked.
  - **(c) The `### Import manifest`'s per-module allowed-import lists as the population.**
    *Loses:* that table is measurably stale at `HEAD` (audit 1a F1; audit 1c C4), so
    adopting it as the ratchet's source requires repairing it first, which is Slice 2 work
    the ratchet would then depend on. *Gains:* one table serves as both prose contract and
    executable manifest.
- **Effect on the shipped test:** under (a) it is one added row (a re-loop through Worker 2
  and Worker 3, already scoped in box 3). Under (b) or (c) it is a larger manifest and a
  spec rewrite; neither is decidable here. Because the missing row is common to all three,
  the re-loop is safe to dispatch before the maintainer answers.
- **Effect on the spec:** deferred to Slice 2 as items 1 and 2 below regardless of which
  option the maintainer picks.

### Escalation B — the narrowed tolerated-meta shape

**Decision: the shipped guard's tolerated shape is correct. It admits no state it should
reject, and no change is owed in this slice.**

- **What the tail now tolerates:** any non-`None` `_mutation_meta` carrying `operation` and
  `optional_fields`. Both incoherent spellings — the attribute absent, and the attribute
  present but `None` (the abstract-base shape) — funnel into one `ConfigurationError`.
  Verified against `docs/builder/BUILD.md` `### Fail-open shapes`: the surviving
  `getattr(mutation_cls, "_mutation_meta", None)` default no longer reaches a permit path,
  so it is no longer a fail-open shape, and `frozenset(meta.optional_fields or ())` is not
  one either — `optional_fields` is `tuple[str, ...] | None` and `None` and `()` are the
  same answer to "which fields are optional", so the `or` fallback has no legitimately-falsy
  left operand carrying a distinct meaning.
- **The narrowing rejects rather than admits.** A duck-typed snapshot missing
  `optional_fields` now raises `AttributeError` at `meta.optional_fields` where the retired
  `getattr` tolerated it. That is a *louder* verdict, not a permitted state — nothing that
  previously failed now passes.
- **Reachability re-derived independently, not accepted from the review.**
  `_assert_schema_runtime_agreement` has exactly one production call site
  (`rest_framework/resolvers.py:2269`, inside the serializer write step), and
  `_assert_field_agreement`'s only other call site is the nested recursion at `:1301`, which
  threads the **same** `mutation_cls`. `mutations/sets.py::_ValidatedMutationMeta` declares
  `operation` and `optional_fields` in `__slots__` and assigns both unconditionally, so no
  bound `SerializerMutation` can reach the tail without them. The one other duck-typed
  `_mutation_meta` shape in the package, `auth/mutations.py::_AuthMutationMetaSnapshot`,
  carries `operation` but not `optional_fields` and cannot reach this call site — an auth
  holder is not a `SerializerMutation` and never enters `_guarded_serializer_write`.
- **The residual is failure-mode quality, not correctness, and tightening it further is a
  maintainer decision.** Requiring `isinstance(meta, _ValidatedMutationMeta)` would convert
  that unreachable-today `AttributeError` into the framework's own `ConfigurationError` —
  but it would also declare the duck-typed snapshot shape **unsupported at this seam**, and
  `auth/mutations.py` deliberately uses one. Whether a duck-typed meta is a supported seam
  is a question about which contract the package offers, so it is escalated, not decided:
  - **Keep the shipped shape** (current). *Loses:* a future flavor reusing the auth-style
    snapshot surfaces as a bare `AttributeError` rather than a named boundary error.
  - **Add an `isinstance` gate.** *Loses:* the duck-typed snapshot stops being a usable
    shape at this seam, and a second boundary is added to a per-field hot path for a state
    nothing can currently produce.
  The cheap half needs no decision and is deferred to Slice 2 (item 6): state the snapshot
  requirement as a spec contract sentence, so a future flavor cannot reach the tail
  unnoticed either way.

### DRY check across this slice and the four preceding audit artifacts

- **No new duplication.** The four audits are read-only and carry no code, so the check is
  whether this slice's code duplicates a shape they identified. It does not: item 1's two
  halves assert different properties (emitted SQL columns vs. the plan object's fields),
  item 3 puts one manifest in one file covering both consumer modules rather than splitting
  it across `test_converter.py` and `test_inputs.py`, item 4 reuses its rejection twin's
  scaffolding and differs in one expression, and item 2 added no helper.
- **The identity-assertion precedent is reused, not copied.**
  `tests/utils/test_inputs.py::test_filter_and_order_input_namespaces_ride_make_set_input_namespace`
  holds the `filters`/`orders` families; the new file holds the serializer flavor. Disjoint
  populations, same instrument. A helper shared across `tests/utils/` and
  `tests/rest_framework/` would serve one call site each — correctly not extracted.
- **Audit 1c's DRY finding 1 stands and this slice adds to it.** Item 2's new
  `ConfigurationError` is a further occurrence of the module's `f"SerializerMutation {…}: "`
  message prefix. Following the file's own 40-site convention is right; consolidating it is
  a whole-file refactor that belongs to the maintainer-routed cleanup card audit 1c already
  named, not to this slice.
- **`_build_serializer_g2_schema` correctly not consolidated further.** The file's
  established idiom is inline schema declaration; extracting a parametrizable builder is the
  same standing candidate Worker 3 recorded, deferred with it.
- **No fail-open shape landed.** Read the whole diff against the catalogue: the one
  surviving `getattr` default reaches a `raise`; `frozenset(... or ())` is answer-equivalent
  (above); the ratchet resolves through `vars(module)` with an explicit `pytest.fail` rather
  than a `getattr` default; the live assertion's `all(...)` runs over a non-empty literal
  tuple so it cannot pass vacuously; `plan = ctx.dst_optimizer_plan` is a direct read that
  raises if the optimizer never stashed.

### Verification runs

- `uv run pytest -n0 tests/rest_framework/ examples/fakeshop/test_query/test_products_api.py --no-cov`
  — **631 passed**, exit 0. No `--cov*` flag.
- `uv run python scripts/check_citations.py --check` — `OK: 963 citations resolve`, which
  covers the new cross-tier `path::QualifiedName` pointer the live comment carries.
- `git diff --stat -- django_strawberry_framework/optimizer/walker.py django_strawberry_framework/rest_framework/inputs.py`
  — prints nothing; both transiently-mutated files are byte-clean against `HEAD` and neither
  is in this slice's diff. No `ACTIVE-MUTATION.json` marker exists anywhere under the repo.
- **Failability records confirmed to EXIST** for all three boundaries, each carrying the
  mutation, the scope as run, the pre-mutation baseline, the listed node ids, `0`
  collection/setup errors, and a byte-compared revert. None is zero-row, so no **why 0**
  judgement is owed. Boundary 2 sits at 2 rows — above the weakly-pinned threshold, with
  both halves of item 1 in the failing set, which is the item's stated closure condition.
- **The seven full-sweep failures are not this slice's.** Not re-derived here: the
  obligation under `docs/builder/BUILD.md` `## Claims are proven mechanically` is that no
  traceback names a file in this diff, which Worker 3 established at a scope containing none
  of the four owned files. Escalated to the maintainer, the only party who can run a clean
  `HEAD` tree. Untouched, unreverted.
- **`docs/builder/build-039-serializer_mutations-0_0_13.md` now carries all three sections**
  Worker 2's note 7 and Worker 3's note 5 reported missing — `## Audit rollup`,
  `## Worker-0 verification of every code-bearing finding`, `## Dispatch-order amendment` —
  at 15,654 B. That note is discharged; the integration pass need not carry it.

### Summary

The slice's four dispatched findings are three-and-a-half closed. `_assert_field_agreement`
no longer fails open when the validated `Meta` snapshot is absent: both incoherent spellings
raise one `ConfigurationError`, the two sibling `getattr` defaults on the same decision path
are retired, and three rows pin the rejection. The G2 "no `.only(...)`" contract now has a
distinguishing assertion in each tier — emitted-SQL columns live, the plan object's
`select_related` / `only_fields` package-internal — and both fail when the walker's G2 gate
is removed, which the retired line structurally could not. The request-identity guard's
tolerated arm is pinned. The DRY import ratchet exists, is parametrized rather than looped,
is measured at `HEAD` rather than transcribed from the spec, and fails on both a same-named
redefinition and a deletion — but it omits `utils/inputs.py::FieldConversionBase`, the
conversion half of the P2.1 promotion the spec's DoD sentence names, so box 3 is un-ticked
and the slice returns for a one-row addition and a re-run of that boundary's proof. No
production change is owed. Both escalations are decided: the ratchet holds the spec's named
promotions (widening to the whole substrate is routed to the maintainer with its
alternatives), and the narrowed tolerated-meta shape is correct — it rejects more than
before and admits nothing new, with the `isinstance` tightening likewise routed as a
contract question.

### Spec changes made (Worker 1 only)

**None made here.** Slice 2 owns every spec and rationale rewrite and runs after this slice
is `final-accepted`. The list below is what this slice's final verification proves the spec
owes, so Slice 2 inherits it rather than re-deriving it. Each names the spec heading and the
corrected contract; none is a chronology — the spec states the current contract directly and
every explanation of what changed belongs in
`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` under the same decision.

1. **`## Slice checklist` → Slice 1 → `**DRY / reuse**` (spec `:640-642`) — the DoD check's
   MECHANISM.** Current text: *"A grep guard that `rest_framework/serializer_converter.py` +
   `rest_framework/inputs.py` **import** these and do not redefine them is the DoD check."*
   Corrected contract: the DoD check is an **object-identity** ratchet at
   `tests/rest_framework/test_dry_import_ratchet.py`, parametrized over a manifest of
   `(consumer module, symbol, owning module)` rows, with the factory-produced one-ledger
   closures held by `__code__` identity instead. State the ceiling honestly in the same
   sentence: the input-kind constants are interned `str`, so their rows catch a deletion and
   a value drift but not a same-valued re-spelling. The "why identity, not grep" reasoning
   (a grep is satisfied by a same-named local and breaks on a legitimate import-style
   change) goes in the rationale companion.
2. **Same bullet — the DoD check's POPULATION.** Whichever option the maintainer picks under
   `### Escalation A`, the sentence must state the population explicitly rather than leaving
   it to the pronoun "these". Under option (a) that is: P1.4's four skeleton symbols, P2.1's
   **both** shapes (`InputFieldSpec` and `FieldConversionBase`), P2.2's trio, P1.3's cache
   pair, P2.3's suffix helper, plus the four input-kind constants and `graphql_camel_name`.
3. **Same bullet — a stale owner.** P2.3 is written as
   *"reuses `mutations/inputs.py::_pascalize_token`"*; the symbol shipped as
   `utils/inputs.py::pascalize_token`. Name the live owner.
4. **`### Import manifest` (spec `:2582`), the `serializer_converter.py` row.** Stale per
   audit 1a F1, re-measured at `HEAD` this pass: `graphql_camel_name` is owned by
   `utils/strings.py`, not `utils/inputs.py`; `utils/relations.py::{relation_kind,
   is_forward_many_to_many, is_many_side_relation_kind}` are not imported at all;
   `types/converters.py::convert_choices_to_enum` is not imported (`::build_enum_from_choices`
   is). Real imports the row does not name include
   `utils/inputs.py::{FieldConversionBase, InputFieldSpec, SCALAR, FILE, RELATION_SINGLE, RELATION_MULTI}`
   and `utils/strings.py::pascal_case`.
5. **`### Import manifest` (spec `:2583`), the `inputs.py` row.** Measured at `HEAD`, six of
   its named symbols are bound in **neither** consumer module —
   `materialize_generated_input_class`, `_pascalize_token`, `build_payload_type`,
   `payload_object_slot`, `relation_input_annotation`, and `build_and_stash_input`, the last
   of which is bound in `rest_framework/sets.py` rather than `rest_framework/inputs.py`
   (`sets.py:72`, called at `:884`). Re-file the row against measured bindings. The
   `resolvers.py` row (audit 1c C4) is unchanged and still owes Worker 1's choice between the
   three resolution paths that audit escalated.
6. **rev6 #1 — the agreement guard's meta arm.** It must describe a **raise**, not a stop:
   `_assert_field_agreement`'s requiredness/annotation tail rejects a mutation reaching it
   with no validated `Meta` snapshot, under both spellings (attribute absent, attribute
   `None`). State the snapshot requirement as a contract in the same place — any object
   reaching that tail carries `operation` **and** `optional_fields` — so a future flavor
   reusing a duck-typed snapshot cannot reach it unnoticed. Audit 1c separately recorded that
   rev6 #1 cites `_assert_injected_field_agreement`, a symbol that does not exist; fix that
   citation in the same pass.
7. **Slice-3 checklist and Definition-of-done item 4 — the G2 tier split.** Both currently
   imply the live tier carries the whole G2 contract. State the split the
   `test_scalars_api.py` precedent already established: the behavioral half is earned live at
   `examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`,
   the plan-object half is package-internal at
   `tests/rest_framework/test_resolvers.py::test_serializer_refetch_keeps_select_related_suppresses_only`
   because the optimizer's stash is introspection state no `/graphql` response carries. Cite
   both by `path::QualifiedName`. `tests/rest_framework/test_resolvers.py`'s module docstring
   already states this split; the spec sentence must agree with it.
8. **Edge case 7 / `## Test plan` — no change owed.** The tolerance arm the spec always
   specified is now pinned. Recorded so Slice 2 does not re-raise it as a gap.

**Not spec edits, carried so they are not lost.** (i) `examples/fakeshop/apps/kanban/constants.py`
goes stale the moment `tests/rest_framework/test_dry_import_ratchet.py` is staged; the
`kanban-tracked-path-constants` hook cannot see an untracked file, so the green
`uvx pre-commit` run is `START.md`'s documented fail-open, not coverage. Remedy at commit
time: `uv run python scripts/build_kanban_tracked_path_constants.py` after `git add`, landed
as a constants-only sync commit. That file is outside this cycle's maintainer-set fence.
(ii) The `f"SerializerMutation {…}: "` message-prefix consolidation and the inline-schema
idiom in `tests/rest_framework/test_resolvers.py` are standing cleanup candidates for their
own cards, not this cycle's.

---

## Build report (Worker 2, pass 2)

Scope of this pass: the single manifest row Worker 1's final verification named as the
over-tick on box 3. Nothing else was reopened — items 1, 2 and 4 stand as built, and their
files were not edited.

### Files touched

- `tests/rest_framework/test_dry_import_ratchet.py` — one row added to `SHARED_BINDINGS`:
  `(serializer_converter, "FieldConversionBase", utils_inputs)`, placed immediately before
  the `InputFieldSpec` row so the pair reads in the order
  `serializer_converter.py` #"from ..utils.inputs import FieldConversionBase, InputFieldSpec"
  binds them. The manifest is 19 identity rows + 2 closure-body rows = 21 node ids. The
  module docstring's opening sentence now names the shared field-spec and conversion
  **shapes** alongside the helpers, because a base class is not a helper and the previous
  wording did not cover the row being added.
- `docs/builder/bld-039-slice-3-code_gaps.md` — this section; box 3 ticked; `Status: built`.
- `docs/builder/temp-tests/039-slice-3/pass2-proofs.json`, `pass2-proofs.md` (scratch) —
  this pass's proof manifest and its emitted record.

### Tests added or updated

- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.FieldConversionBase]`
  — pins that `rest_framework/serializer_converter.py`'s `FieldConversionBase` **is** the
  `utils/inputs.py` class object, so a local body-copy of the conversion base — which
  behaves identically and therefore breaks no behavioral row anywhere in the tree — fails
  here instead of shipping silently.

**Identity measured first, from a real import, not taken from the plan or the spec.** Under
`DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop` with `django.setup()`:
`"FieldConversionBase" in vars(serializer_converter)` → `True`;
`"FieldConversionBase" in vars(utils_inputs)` → `True`;
`vars(serializer_converter)["FieldConversionBase"] is vars(utils_inputs)["FieldConversionBase"]`
→ `True`; the bound object's `__module__` is `django_strawberry_framework.utils.inputs`. The
same probe confirmed the name was absent from `SHARED_BINDINGS` before the edit (18 identity
rows, 2 closure rows). The spec's `### Import manifest` was not consulted as a source for the
binding: Worker 1 measured both of its rows stale.

### Validation run

- `uv run ruff format tests/rest_framework/test_dry_import_ratchet.py` — pass (`1 file left
  unchanged`; the pre-existing COM812-vs-formatter warning is unrelated to this file).
- `uv run ruff check --fix tests/rest_framework/test_dry_import_ratchet.py` — pass
  (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py tests/rest_framework/test_dry_import_ratchet.py`
  — pass (`Fixed 0 file(s).`).
- `git status --short` after both ruff invocations: `M django_strawberry_framework/rest_framework/resolvers.py`,
  `M docs/SPECS/spec-039-serializer_mutations-0_0_13.md`, `M examples/fakeshop/test_query/test_products_api.py`,
  `M tests/rest_framework/test_resolvers.py`, plus the untracked `bld-*` / `build-039-*` /
  rationale-companion artifacts and the untracked `tests/rest_framework/test_dry_import_ratchet.py`.
  All slice-intended or owned by Worker 1 (the spec edit). The concurrent `spec-050` files
  that were dirty at the start of this pass are no longer listed — that session committed
  during this pass; nothing of theirs was edited or reverted here. The two production files
  this pass transiently mutated for the proofs (`rest_framework/inputs.py`,
  `rest_framework/serializer_converter.py`) are absent from the list, which is an independent
  second witness to the byte-compared restores below.
- Focused run: the proof tool's own unmutated baseline is the focused run for this pass —
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/rest_framework/`
  → `497 passed` (exit 0), twice, once before each mutation. 497 = the 496 rows the prior
  pass recorded plus this pass's one new parametrized row. No `--cov*` flag anywhere.

### Failability proofs

Produced by
`uv run python scripts/prove_failability.py docs/builder/temp-tests/039-slice-3/pass2-proofs.json --scratch-root <scratchpad>/failability --output docs/builder/temp-tests/039-slice-3/pass2-proofs.md`;
run exit code **0** (every entry proved, none weakly pinned, no collection or setup error).
Anchors were checked with `--check-anchors-only` **before** any copy or mutation: both matched
exactly once. The scratch root is outside the repository; no `ACTIVE-MUTATION.json` marker
remains.

- `django_strawberry_framework/rest_framework/inputs.py::_serializer_shape_build_cache` —
  **the re-run of the boundary's prior proof, at the scope the prior pass recorded**, so the
  recorded node-id set matches the shipped file. Mutation applied: after the module tail
  `_serializer_shape_build_cache, clear_serializer_shape_build_cache = make_shape_build_cache()`
  (past every call site, so the change is inert at runtime), `pascalize_token`,
  `make_input_namespace` and `make_shape_build_cache` re-bound to same-named local delegating
  wrappers over the promoted objects; scope as run:
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/rest_framework/`;
  pre-mutation state of that scope: green (`497 passed`, pytest exit 0), 0 pre-existing
  failing rows differenced out; failing node ids:
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_input_namespace]`,
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_shape_build_cache]`,
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.pascalize_token]`;
  collection/setup errors: **0**; revert proved by byte-comparison:
  `filecmp.cmp(shallow=False)` True and sha256 `c97f01100b3bd840...` == `c97f01100b3bd840...`
  against the pre-mutation copy. Node-id set identical to the prior pass's record; only the
  scope's pre-mutation total moved (496 → 497), which is the new row.
- `django_strawberry_framework/rest_framework/serializer_converter.py::SerializerFieldConversion`
  — **the converter half of the ratchet, which no prior proof had mutated**: the earlier
  record removed shared bindings only from `rest_framework/inputs.py`, so every
  `serializer_converter` row in the manifest — the new one included — was unproven. Mutation
  applied: the import line
  #"from ..utils.inputs import FieldConversionBase, InputFieldSpec" replaced by aliased
  imports plus three same-named local stand-ins — `FieldConversionBase` as a trivial subclass
  of the promoted class (inert: the module reads that name only in the
  `class SerializerFieldConversion(...)` statement), and `InputFieldSpec` and
  `convert_with_mro` as delegating wrappers, so every call still reaches the promoted object
  and only identity moves; scope as run:
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/rest_framework/`;
  pre-mutation state of that scope: green (`497 passed`, pytest exit 0), 0 pre-existing
  failing rows; failing node ids:
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.convert_with_mro]`,
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.FieldConversionBase]`,
  `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.InputFieldSpec]`
  — **the new row is in the failing set**, and the other 494 rows passed, which is the
  evidence the stand-ins were behavior-preserving and therefore invisible to every behavioral
  test; collection/setup errors: **0**; revert proved by byte-comparison:
  `filecmp.cmp(shallow=False)` True and sha256 `8e5fb7bdbc0b35e3...` == `8e5fb7bdbc0b35e3...`
  against the pre-mutation copy.

Neither entry is zero-row and neither is at 1 row, so no **why 0** judgement is owed and
nothing here grades weakly pinned.

### Hot-path budget

Not applicable to this pass: it adds no production code and no per-request work. The plan's
hot-path declaration was discharged by the first pass and its numbers are unchanged, because
no production file was edited here.

### Floor verification

Owned by the final gate per the plan's declaration; unchanged by this pass, which touches no
Django / Strawberry integration seam.

### Implementation notes

- **Row placement, not appended at the end.** The new row sits directly above
  `(serializer_converter, "InputFieldSpec", utils_inputs)` so the manifest mirrors the single
  import statement that binds both names. A reader diffing the manifest against
  `serializer_converter.py`'s import block can do it line for line.
- **The docstring's opening sentence was widened by three words.** It previously enumerated
  "helpers" and the four kind constants; a base class is neither, so the sentence would have
  read as a manifest narrower than the manifest. The invariant is stated, with no reference
  to how the row came to be added.
- **The proof mutates the shared-import line rather than appending at the module tail.** The
  tail trick used for `inputs.py` works because those three names are read at call time;
  `FieldConversionBase` is read exactly once, at class-creation time, so a tail rebinding
  would move the module attribute without ever reaching `SerializerFieldConversion` — a
  weaker mutation that removes less. Mutating the import site removes the binding for every
  reader, and the subclass stand-in keeps `isinstance` against the promoted base true, which
  is what keeps the mutation boundary-removing rather than behavior-perturbing.
- **`is` on a class object catches what prose cannot**, and unlike the four interned-string
  kind constants, a class row also catches a same-valued re-spelling: two structurally
  identical class statements are never the same object.

### Notes for Worker 3

- The manifest is now 19 identity rows and 2 closure-body rows (21 node ids). The plan's
  step 9 says "20 node ids total", written against the 18-row table; that figure is the
  plan's, and the plan is Worker 1's to amend.
- Both failability entries are inside the mandatory independent re-run floor (3 rows each).
  The manifest for a re-run is `docs/builder/temp-tests/039-slice-3/pass2-proofs.json`; it
  carries the prior pass's `inputs.py` entry verbatim, so a set-difference against the
  earlier record is meaningful.
- No production file changed in this pass. `git diff -- django_strawberry_framework/rest_framework/inputs.py django_strawberry_framework/rest_framework/serializer_converter.py`
  is empty, which is available as a second check on both restores.

### Notes for Worker 1 (spec reconciliation)

The pass-1 notes stand unchanged; this adds one bookkeeping item and one plan-figure
correction. No new spec amendment is owed — Worker 1's `### Escalation A` already decided the
population, and this pass implements exactly its option (a) remainder.

- **`docs/builder/bld-039-slice-3-code_gaps.md` `### Implementation steps` → `#### Item 3 — the DRY import ratchet`, step 9.** Current wording:
  *"20 node ids total."* Recommended replacement: *"21 node ids total."* Table A in step 8 is
  correspondingly 19 rows, the added row being
  `| rest_framework/serializer_converter.py | FieldConversionBase | utils/inputs.py | P2.1 |`.
  This is the build artifact's own plan text, not the spec; recorded here because Worker 1
  owns that section and the figure is now stale by one.
- **Already-filed amendment 2 covers the spec side.** The pass-1 note on
  `## Slice checklist` → Slice 1 → `**DRY / reuse**` already asks that the DoD sentence name
  P2.1's **both** shapes explicitly instead of leaning on "these"; the shipped manifest now
  matches that wording, so no further change is owed there.

---

## Review (Worker 3, pass 2)

Scope of this re-review: the single manifest row Worker 1's final verification named as the
over-tick on box 3, and nothing else. Boxes 1, 2 and 4 were accepted in
`## Review (Worker 3)` and re-confirmed by Worker 1's box-by-box audit; they are not
reopened here, only checked for pass-2 disturbance.

### Independent failability re-run — mutations recorded BEFORE they are applied

Both pass-2 entries carry a recorded failing-row count of **3**, so both are inside the
mandatory re-run floor (`docs/builder/worker-3.md` `### Reading is necessary, not
sufficient: the failability proof`). The re-run subset is therefore **both entries**, and
the accepted-on-Worker-2's-record subset is **empty**.

Manifest for this pass: `docs/builder/temp-tests/039-slice-3/w3-r2-proofs.json`, a byte
copy of Worker 2's `pass2-proofs.json` (verified by `cmp`), run under a Worker-3-only name
so the builder's record is never overwritten. Scratch root outside the repository. Anchors
checked with `--check-anchors-only` before any copy or mutation.

**Mutation 1 — `django_strawberry_framework/rest_framework/inputs.py::_serializer_shape_build_cache`.**
Anchor: the module tail
#"_serializer_shape_build_cache, clear_serializer_shape_build_cache = make_shape_build_cache()".
After it, `pascalize_token`, `make_input_namespace` and `make_shape_build_cache` are re-bound
to same-named local delegating wrappers over the promoted objects. Past every call site, so
the mutation is inert at runtime and moves identity only. Scope as run:
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/rest_framework/`.

**Mutation 2 — `django_strawberry_framework/rest_framework/serializer_converter.py::SerializerFieldConversion`.**
Anchor: the import line
#"from ..utils.inputs import FieldConversionBase, InputFieldSpec". Replaced by aliased
imports of the same three promoted objects plus three same-named local stand-ins:
`FieldConversionBase` as a trivial subclass of the promoted class, `InputFieldSpec` and
`convert_with_mro` as delegating wrappers. Scope as run: the same
`tests/rest_framework/` invocation.

Both mutations are applied and reverted by `scripts/prove_failability.py` one entry at a
time, with the restore proved by byte comparison against the pre-mutation copy.

### Independent re-run result — node-id SETS, at Worker 2's recorded scopes

`uv run python scripts/prove_failability.py docs/builder/temp-tests/039-slice-3/w3-r2-proofs.json --scratch-root <scratchpad>/w3-r2-failability --output docs/builder/temp-tests/039-slice-3/w3-r2-proofs.md`
— run exit code **0**, both entries proved, neither weakly pinned, **0** collection/setup
errors on either. Anchors pre-checked: both matched exactly once, so no live mutation was
already in the tree.

**Boundary 1 — `rest_framework/inputs.py::_serializer_shape_build_cache`.** Pre-mutation
state of the scope: green, `497 passed`, pytest exit 0, 0 pre-existing failing rows
differenced out. Mutant: `3 failed, 494 passed`, pytest exit 1. Failing node ids:

- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_input_namespace]`
- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.make_shape_build_cache]`
- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[inputs.pascalize_token]`

**Set identical to Worker 2's pass-2 record, and identical to the pass-1 record.** Restore:
`filecmp.cmp(shallow=False)` True, sha256 `c97f01100b3bd840...` == `c97f01100b3bd840...`.

**Boundary 2 — `rest_framework/serializer_converter.py::SerializerFieldConversion`.**
Pre-mutation state of the scope: green, `497 passed`, pytest exit 0, 0 pre-existing failing
rows. Mutant: `3 failed, 494 passed`, pytest exit 1. Failing node ids:

- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.FieldConversionBase]`
- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.InputFieldSpec]`
- `tests/rest_framework/test_dry_import_ratchet.py::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.convert_with_mro]`

**Set identical to Worker 2's record; the pass's new row is in it.** Restore:
`filecmp.cmp(shallow=False)` True, sha256 `8e5fb7bdbc0b35e3...` == `8e5fb7bdbc0b35e3...`.

Both sha256 prefixes match the ones Worker 2 recorded, which corroborates that the two
passes mutated the same pristine bytes — a check the row counts alone cannot make. After
the run, `git diff --stat -- django_strawberry_framework/rest_framework/inputs.py
django_strawberry_framework/rest_framework/serializer_converter.py` prints nothing and no
`ACTIVE-MUTATION.json` remains under the scratch root.

**Where the second pair of eyes landed:** re-run independently — **both** pass-2
boundaries. Accepted on Worker 2's record alone — **none**.

### The 494-passing-rows claim, re-derived rather than accepted

Worker 2's argument for the ratchet existing at all is that the converter stand-ins were
behavior-preserving and therefore invisible to every behavioral test. Re-derived from my own
mutant run, not read from the build report: `3 failed, 494 passed`, and all three failing
rows are ratchet rows. **No behavioral row in `tests/rest_framework/` moved under the
mutation.** 494 + 3 = 497 = the unmutated total, so the arithmetic closes with no row
unaccounted for.

The mechanism is visible in the source, not only in the count:
`django_strawberry_framework/utils/converters.py:189` #"if isinstance(result, FieldConversionBase):"
is the one behavioral reader of the promoted base, and the mutant's stand-in is a **subclass**
of the promoted class, so that `isinstance` stays true. The mutation therefore removes the
binding identity while leaving every behavioral path intact — boundary-removing, not
boundary-perturbing, which is exactly the shape a ratchet row must catch and no behavioral
test can.

### The added row is real, and not an accident of import order

Measured from a real import under `DJANGO_SETTINGS_MODULE=config.settings
PYTHONPATH=examples/fakeshop` with `django.setup()`, independently of Worker 2's probe:

- `"FieldConversionBase" in vars(serializer_converter)` → `True`
- `"FieldConversionBase" in vars(utils_inputs)` → `True`
- `vars(serializer_converter)["FieldConversionBase"] is vars(utils_inputs)["FieldConversionBase"]`
  → `True`; `id()` equal. **Matches Worker 2's measurement exactly.**

Not accidental: `inspect.getsourcefile` on the bound object resolves to
`django_strawberry_framework/utils/inputs.py` and its `__module__` is
`django_strawberry_framework.utils.inputs`, so `utils_inputs` is the definer and not a
re-exporter; `serializer_converter.py:97` binds it by an explicit
`from ..utils.inputs import FieldConversionBase, InputFieldSpec`, not by a star import or a
transitive re-export. Both flavors subclass the one object
(`SerializerFieldConversion.__bases__` and `FormFieldConversion.__bases__` are each
`(utils.inputs.FieldConversionBase,)`), which is the promotion the row pins.

The whole manifest was re-derived executably as well — every one of the 19 identity rows
resolves to a genuinely identical binding (`non-identical rows: []`) and both closure rows
share a `__code__` object. So the added row did not arrive alongside a stale one.

### Still parametrized, never looped; population not widened

`uv run pytest --no-cov -q --collect-only tests/rest_framework/test_dry_import_ratchet.py`
→ **21 tests collected**, each an individually addressable node id
(19 `test_serializer_flavor_binds_the_shared_object_itself[...]` + 2
`test_serializer_flavor_closures_share_one_body[...]`). Two module-level tuples driving two
`@pytest.mark.parametrize` decorators; no `for` loop inside any test body, so the ratchet's
own failability is not capped at 1.

Population discipline holds. 19 identity rows − the added `serializer_converter.FieldConversionBase`
= the 18 rows pass 1 shipped and this reviewer verified then; the row set is otherwise
unchanged, and `SHARED_CLOSURE_BODIES` is untouched at 2. Nothing from the
`### Escalation A` option-(b) substrate was pulled in: `inputs.optional_input_field`,
`inputs.resolve_effective_fields`, `inputs.guard_dropped_required`,
`inputs.iter_input_field_collisions`, `inputs.generated_input_type_name`,
`serializer_converter.pascal_case`, `serializer_converter.convert_scalar`,
`serializer_converter.scalar_for_field` all remain outside the manifest. The pass implemented
Escalation A option (a)'s remainder and stopped there.

### Pass 2 did not disturb items 1, 2 and 4

- `django_strawberry_framework/rest_framework/resolvers.py` — `git diff` read in full: one
  hunk, 17 lines, entirely item 2 (`if meta is None:` raising `ConfigurationError`, the two
  sibling `getattr` defaults retired, the invariant comment). Nothing pass-2-shaped.
- `examples/fakeshop/test_query/test_products_api.py` — `git diff` read in full: one hunk,
  22 lines, entirely item 1's live half (`refetch_select` off the captured SQL, the five
  `undeferred` columns, the retired `SerG2Widget` `values_list` assertion gone).
- `tests/rest_framework/test_resolvers.py` — the diff adds exactly the six definitions pass 1
  recorded (`test_merged_kwargs_override_echoing_the_same_request_object_is_tolerated`, the
  three `test_agreement_guard_rejects_*` rows, `_build_serializer_g2_schema`,
  `test_serializer_refetch_keeps_select_related_suppresses_only`) and grepping the diff for
  `FieldConversionBase` / `SHARED_BINDINGS` / `ratchet` returns nothing.

All three findings' shipped content re-confirmed present at the spellings Worker 1 quoted.

### High:

None.

### Medium:

None.

### Low:

#### The widened docstring sentence left a ragged wrap

`tests/rest_framework/test_dry_import_ratchet.py:3-8`. Inserting "and the shared field-spec
and conversion shapes" into the opening sentence shifted the fill without the paragraph being
re-wrapped, so line 6 ends at roughly column 46 (#"constants are single-sourced in
`utils/inputs.py`. That") while the lines around it run to the margin. Purely cosmetic: `ruff
format` does not reflow docstring prose, `ruff check` and
`scripts/check_trailing_commas.py --check` both pass on the file, and no gate sees it.

**Not held, and the reason is recorded rather than left implicit:** the content is correct
and complete, and a re-loop through Worker 2 to re-wrap three lines of a docstring costs a
full build/review pass against a defect with no behavioral or gate consequence. Routed to
`### Notes for Worker 1 (spec reconciliation)` as a one-line cleanup to fold into whatever
pass next edits this file.

### DRY findings

- **Nothing new duplicated.** The pass adds one tuple element to an existing manifest and
  three words to an existing docstring sentence. No helper, no constant, no branch.
- **My pass-1 `### DRY findings` was wrong on one sentence and Worker 1 corrected it
  correctly.** It said the shipped manifest "is exactly the population the spec's
  `**DRY / reuse**` bullet enumerates"; it was that population **minus**
  `FieldConversionBase`, which my own census had listed under "10 further bindings" and I
  mis-classified as outside the spec's named promotions rather than inside P2.1's second
  shape. The correction is now shipped. I also accept Worker 1's second point: the "10"
  figure was an artifact of a census that compared against three owner modules only, so it
  understates its own option-(b) population and no figure from it should be republished.
- **The row does not create a second population to maintain.** `SHARED_BINDINGS` remains the
  single manifest for both consumer modules, read against the source, with the docstring
  stating its own scope honestly ("the manifest is the population this guard covers").
- **No existence challenge.** The manifest is still the pass's only abstraction, with two
  real consumers and no indirection layer over anything.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the
re-export list are unchanged; this pass adds no public export. No spec authorization needed.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; this pass did not modify docs/release/KANBAN/archive surfaces. Its only
non-test edits are to this artifact and to gitignored scratch under
`docs/builder/temp-tests/039-slice-3/`.

### Gate re-verification

- `uv run ruff format --check tests/rest_framework/test_dry_import_ratchet.py` — `1 file
  already formatted`.
- `uv run ruff check tests/rest_framework/test_dry_import_ratchet.py` — `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --check tests/rest_framework/test_dry_import_ratchet.py`
  — exit 0.
- No `--cov*` flag was used in any run this pass.

### Test-staleness sweep, run independently of the slice's file list

Run against the tree, not against `### Files touched`. Neither `BUILD.md`
`### Test staleness a focused run cannot see` shape is present in this pass: no example-model
field was added, removed or renamed, and no wire shape was converted. The one symbol the pass
newly asserts on was swept across all three test trees anyway —
`grep -rn 'FieldConversionBase' tests/ examples/fakeshop/apps/ examples/fakeshop/test_query/ examples/fakeshop/tests/`
returns `tests/utils/test_converters.py` (5 hits, all against the promoted
`utils/inputs.py` class and unaffected) and the new manifest row. Nothing stranded.

### The seven full-sweep failures still reproduce, and they are not this slice's

Worker 0's dispatch expected the concurrent `spec-050` commit at `4c483b6b` to have cleared
them. It did not. `uv run pytest --no-cov -q -p no:cacheprovider --tb=no -rfE` over all trees
at the current tree: **7 failed, 7630 passed, 40 skipped**, the same seven Worker 2 recorded
in pass 1:

- `tests/test_list_field.py::test_list_field_direct_call_schema_name_fallback_and_definition_lookup`
- `tests/test_list_field.py::test_list_field_post_orderset_validator_arms`
- `tests/test_list_field.py::test_list_field_constructor_validation_precedence`
- `tests/test_list_field.py::test_list_arguments_immutability_and_slots`
- `tests/utils/test_querysets.py::test_validate_post_orderset_result_routing_hints_none_vs_empty`
- `tests/orders/test_sets.py::test_input_has_active_terms_hostile_eq_and_repr`
- `examples/fakeshop/test_query/test_list_field_api.py::test_holder_materialized_and_nullable_none_fields`

**Not attributable to this cycle, established mechanically rather than asserted.** The tree's
only code deviations from `HEAD` are `rest_framework/resolvers.py`,
`tests/rest_framework/test_resolvers.py`,
`examples/fakeshop/test_query/test_products_api.py` and the new
`tests/rest_framework/test_dry_import_ratchet.py`;
`grep -ln 'rest_framework' <the four failing test files>` returns nothing, so none of them
reaches this cycle's one production edit. The failures land inside `list_field.py`
(e.g. `::_handle_non_queryset_rejections_sync` raising
`Invalid argument 'orderBy' on branchesMaterialized: ...` against a test expecting the
snake-case `branches_materialized` spelling), which is `spec-050` territory and is red **at
the committed `4c483b6b`**. Escalated below, not acted on — `BUILD.md` permits hand-off only
for genuinely out-of-build, pre-existing-at-HEAD issues, and this is one.

### What looks solid

- **The right shape of mutation for the new row.** Mutating the import site rather than the
  module tail is not a stylistic choice — `FieldConversionBase` is read exactly once, at
  class-creation time, so a tail rebinding would have moved the module attribute without ever
  reaching `SerializerFieldConversion` and would have proved a weaker boundary. Worker 2 named
  that reasoning in `### Implementation notes` before I could ask for it.
- **The converter half was genuinely unproven before this pass, and Worker 2 said so.** The
  pass-1 record mutated `inputs.py` only, so every `serializer_converter` row rested on
  nothing. Volunteering a second entry that was not asked for is the opposite of the
  corner-cutting `BUILD.md` warns proof overload produces.
- **A subclass stand-in, not a lookalike.** Keeping `isinstance` true against the promoted
  base is what makes the mutant behavior-preserving, which is what makes the 494-passing
  rows evidence rather than noise.
- **Row placement mirrors the import statement.** The new row sits immediately above
  `(serializer_converter, "InputFieldSpec", utils_inputs)`, so the pair reads in the order
  `serializer_converter.py:97` binds them and the manifest can be diffed against the source
  line for line.
- **Scope held.** One file, one row, one docstring sentence. Items 1, 2 and 4 were not
  reopened and their files were not touched.

### Temp test verification

- No new temp test was written this pass; reading plus the two mutant runs answered every
  question.
- Scratch used: `docs/builder/temp-tests/039-slice-3/w3-r2-proofs.json` (a `cmp`-verified byte
  copy of Worker 2's `pass2-proofs.json`, run under a Worker-3-only name so the builder's
  record is never overwritten) and `docs/builder/temp-tests/039-slice-3/w3-r2-proofs.md` (the
  emitted record). Both confirmed gitignored via `git check-ignore -v`
  (`.gitignore:192 docs/builder/temp-tests/`).
- Disposition: **kept** as this pass's proof record, to be cleared with the cycle by
  `scripts/clean_up.py`. Nothing to promote — no temp test caught a behavior bug.

### Notes for Worker 1 (spec reconciliation)

1. **The plan's own figure is now stale by one, and it is yours to amend.**
   `### Implementation steps` → `#### Item 3 — the DRY import ratchet`, step 9 still reads
   *"20 node ids total."*; the shipped file collects **21**. Step 8's Table A is
   correspondingly 19 rows. Worker 2 filed the same item; confirming it independently because
   the artifact currently contradicts itself between plan and build report, and Worker 3 does
   not edit the plan.
2. **Escalated: the seven `spec-050` failures are red at the committed `4c483b6b`, not
   cleared by it.** Evidence and node ids above. This is a maintainer decision, not a slice
   decision, and the resolution paths are: (a) hand off to a separate session against
   `list_field.py` / `orders/sets.py` / `utils/querysets.py` — the `BUILD.md`-sanctioned route
   for a pre-existing-at-HEAD issue; (b) hold `spec-039`'s final gate until they are green,
   which blocks this cycle on unrelated work; (c) accept the cycle with the red rows recorded.
   I have not acted on any of them. Worth naming for whoever picks: the live failure text
   shows a camelCase-vs-snake_case spelling disagreement in a `ListArgumentError` message
   (`'orderBy' on branchesMaterialized` vs a test expecting `branches_materialized`), so at
   least one of the seven looks like a one-line message-spelling decision rather than a
   design question.
3. **Cosmetic, no gate, not held (the Low above).** The widened docstring sentence at
   `tests/rest_framework/test_dry_import_ratchet.py:3-8` leaves a ragged wrap. Fold the
   re-wrap into whatever pass next edits that file; it does not justify a re-loop on its own.
4. **The forms flavor has no equivalent ratchet, and that is a population question you
   already routed.** `django_strawberry_framework/forms/converter.py:71` imports the same
   `FieldConversionBase` and `::FormFieldConversion` subclasses it, entirely uncovered by
   `SHARED_BINDINGS`, whose name and docstring scope it to the serializer flavor. That is
   correct against `spec-039`'s scope and I raise no finding; recording it only so the
   maintainer answering `### Escalation A` knows the option-(b) substrate has a second axis
   (which flavors) besides which symbols.

### Review outcome

`review-accepted`. The over-tick Worker 1 identified is closed by exactly one manifest row;
the identity it asserts was re-derived independently and matches Worker 2's measurement; both
failability entries were re-run at Worker 2's recorded scopes and both node-id **sets** match
his record exactly, with 0 collection/setup errors, byte-proved restores whose sha256
prefixes also match, and neither entry weakly pinned; the manifest is still parametrized at
21 node ids and was not widened beyond the single row; and items 1, 2 and 4 are byte-for-byte
undisturbed. The one Low finding is cosmetic, has no gate, and is recorded as not held with
the reason above. The seven `spec-050` failures are escalated as pre-existing at `HEAD`, not
charged to this slice.

---

## Final verification (Worker 1, pass 2)

**Outcome: `final-accepted`.** The over-tick is closed by the one row it needed; boxes 1, 2
and 4 are byte-for-byte the diff this pass audited before, and nothing new landed with the
row. Both escalations stand as decided in the prior pass and are not re-opened here. One
new escalation is recorded — `HEAD` itself is red, and this cycle did not make it so.

### Box 3 — the verdict, re-derived rather than read from the review

**`- [x]` STANDS. The over-tick is repaired.**
`tests/rest_framework/test_dry_import_ratchet.py:46` now carries
`(serializer_converter, "FieldConversionBase", utils_inputs),`, placed directly above the
`InputFieldSpec` row so the pair reads in the order
`django_strawberry_framework/rest_framework/serializer_converter.py`
#"from ..utils.inputs import FieldConversionBase, InputFieldSpec" binds them. Manifest is
19 identity rows + 2 closure rows.

Measured this pass, from a real import under `DJANGO_SETTINGS_MODULE=config.settings
PYTHONPATH=examples/fakeshop` with `django.setup()`, not accepted from either worker's
record:

- Every one of the 19 identity rows resolves to a genuinely identical binding —
  `non-identical rows: []` — and both closure rows share one `__code__`.
- `vars(serializer_converter)["FieldConversionBase"] is utils_inputs.FieldConversionBase`
  → `True`; the bound object's `__module__` is
  `django_strawberry_framework.utils.inputs`, so `utils/inputs.py` is the definer and not a
  re-exporter.
- Both flavors subclass the one object:
  `SerializerFieldConversion.__bases__` and `forms/converter.py::FormFieldConversion`'s
  `__bases__` are each `(utils.inputs.FieldConversionBase,)`. That is the P2.1 conversion
  promotion the row pins, and the reason a body-copy in `serializer_converter.py` would
  break no behavioral row.

**Independent negative control on the new row, run without mutating any repository file.**
An out-of-repo pytest plugin (scratchpad, loaded by `PYTHONPATH` + `-p`) rebound
`serializer_converter.FieldConversionBase` to a same-named trivial subclass of the promoted
class — the exact regression the row exists to catch, and one that keeps
`utils/converters.py` #"if isinstance(result, FieldConversionBase):" true so no behavioral
path moves. `uv run pytest -n0 --no-cov -q -p no:cacheprovider -p w1_fcb_mutant
tests/rest_framework/test_dry_import_ratchet.py` → **1 failed, 20 passed**, the single
failure being
`::test_serializer_flavor_binds_the_shared_object_itself[serializer_converter.FieldConversionBase]`
with the manifest's own message. This is a third measurement of the row's failability,
taken by a different instrument than either worker's (`prove_failability.py` mutating the
import site); it agrees with both, and it leaves the tree untouched by construction —
`git status --short` and `git diff` over the two production files are unchanged by it.

### The other three boxes — undisturbed, re-checked against the diff

- **Box 1 `- [x]`.** `git diff -- examples/fakeshop/test_query/test_products_api.py` is one
  22-line hunk: `refetch_select` taken off the already-captured `sql`, the five
  `"products_item"."<column>"` names asserted through `all(...)` over a non-empty literal
  tuple, the retired `values_list` line gone rather than supplemented, and the cross-tier
  pointer to the package half. `tests/rest_framework/test_resolvers.py` adds
  `_build_serializer_g2_schema` and
  `::test_serializer_refetch_keeps_select_related_suppresses_only`.
- **Box 2 `- [x]`.** `git diff -- django_strawberry_framework/rest_framework/resolvers.py`
  is one 17-line hunk, entirely item 2: `if meta is None:` raising `ConfigurationError`,
  `getattr(meta, "operation", "create")` → `meta.operation`,
  `frozenset(getattr(meta, "optional_fields", None) or ())` →
  `frozenset(meta.optional_fields or ())`, plus the invariant comment. It is the only
  production edit in the slice.
- **Box 4 `- [x]`.** `::test_merged_kwargs_override_echoing_the_same_request_object_is_tolerated`
  is present with the three `test_agreement_guard_rejects_*` rows; the six added
  definitions are exactly the six pass 1 recorded, and no seventh.

No box is left `- [ ]`. Nothing is deferred out of the checklist.

### DRY check across this slice and the four preceding audit artifacts

- **Pass 2 introduced nothing to duplicate.** One tuple element and three words in an
  existing docstring sentence; no helper, constant, branch, or production line.
- **The row created no second population.** `grep -rl 'SHARED_BINDINGS\|SHARED_CLOSURE_BODIES'
  tests/ examples/` returns exactly one file. The other `FieldConversionBase` references in
  the test trees are `tests/utils/test_converters.py`, where it is a fixture base class for
  converter behavior (`class _Conv(FieldConversionBase)`, and two `__code__` comparisons
  over `make_scalar_converter` / `make_kind_converter`) — a disjoint instrument on a
  disjoint question, not a competing manifest.
- **The prior pass's DRY conclusions are unchanged**, since no file they concerned was
  edited: the two halves of item 1 assert different properties, item 4 reuses its rejection
  twin's scaffolding, item 2 added no helper, and the identity-assertion precedent at
  `tests/utils/test_inputs.py::test_filter_and_order_input_namespaces_ride_make_set_input_namespace`
  holds a disjoint family with the same instrument.
- **No fail-open shape landed this pass.** The added row resolves through `vars(module)`
  with an explicit `pytest.fail` on absence rather than a `getattr` default, so a dropped
  symbol fails loudly instead of comparing `None is None`.
- **Three audit-side consolidation candidates remain open and are not this slice's** —
  recorded so they keep a named home. Audit 1a `### DRY findings`: the duplicated
  nested-serializer error-message tail spelled twice in
  `django_strawberry_framework/rest_framework/inputs.py`
  (`::_fingerprint_nested`, `::_resolve_nested_field`), and the provisional input-type-name
  expression derived twice in the same file (`::resolve_injected_field_specs`,
  `::build_serializer_input_class`) where a divergence is a live-failure mode. Audit 1c
  `### DRY findings` 1: the `f"SerializerMutation {…}: "` message prefix, now at one more
  site. None was dispatched to this cohort and this slice does not own `inputs.py`; the
  cross-slice integration pass should confirm each carries an owning card before the cycle
  closes.

### Verification runs

- `uv run pytest -n0 tests/rest_framework/ examples/fakeshop/test_query/test_products_api.py --no-cov`
  — **632 passed**, exit 0. Exactly one more row than the 631 this scope carried at the
  prior pass, which is the added parametrization and nothing else. No `--cov*` flag.
- `uv run python scripts/check_citations.py --check` — `OK: 963 citations resolve`,
  identical to the prior pass's figure: pass 2 added no `path::Symbol` citation.
- `git diff --stat -- django_strawberry_framework/rest_framework/inputs.py
  django_strawberry_framework/rest_framework/serializer_converter.py` — prints nothing.
  Both files transiently mutated for the failability proofs are byte-clean against `HEAD`;
  no `ACTIVE-MUTATION.json` exists anywhere under the repository.
- `git status --short` — the four modified files are `rest_framework/resolvers.py`,
  `test_products_api.py`, `tests/rest_framework/test_resolvers.py` and the spec (Slice 0's
  rationale extraction, not this slice), plus the untracked artifacts and the new ratchet
  file. The concurrent `spec-050` session's files are gone from the list; it committed at
  `4c483b6b`. Nothing of theirs was edited or reverted.
- **Failability records confirmed to EXIST** for both pass-2 entries, each carrying the
  mutation, the scope as run, the pre-mutation baseline (`497 passed`, 0 rows differenced
  out), the listed failing node ids, `0` collection/setup errors, and a byte-compared
  revert with matching sha256 prefixes. Neither is zero-row and neither sits at 1, so no
  **why 0** judgement is owed and nothing grades weakly pinned. Worker 3 re-ran both
  independently and reports set-identical results; my own negative control above is a third
  instrument on the row that mattered.
- `grep -rn 'TODO(spec-039' . --include='*.py' --include='*.md'` — the only hits are the
  spec's and the rationale companion's prose *describing* the anchor convention. No live
  staged anchor exists in any source file, so none is stranded by this slice.

### Escalation A — carried, not re-decided, with one datum added

The population question — whether the ratchet should hold the spec's named promotions or
the whole measured shared substrate — remains the maintainer's, with the three options and
what each loses recorded in `### Escalation A` of the prior pass. It does not block
`final-accepted`: the added row is in **every** candidate population, which is what made
the re-loop safe to dispatch ahead of the answer.

One datum arrived with pass 2 and belongs beside the options rather than inside them.
Worker 3's note 4: `django_strawberry_framework/forms/converter.py` imports the same
`FieldConversionBase` and `::FormFieldConversion` subclasses it, and no ratchet covers the
forms flavor at all — `SHARED_BINDINGS`'s name and docstring scope it to the serializer
flavor. That is correct against `spec-039`'s scope and is not a finding. It means the
option-(b) substrate has a **second axis** (which flavors) besides which symbols, so
whoever answers the escalation is answering two questions, not one.

### Escalation B — carried as decided

The narrowed tolerated-meta shape is correct: it converts two incoherent spellings into one
`ConfigurationError` and admits nothing it should reject. The `isinstance` tightening stays
routed to the maintainer as a seam-support question. Not re-litigated here; pass 2 touched
no production file.

### Escalation C — `HEAD` is red, and this cycle did not make it red

Recorded for the maintainer and explicitly **not** charged to this slice or resolved in it.

- **Two scopes, two figures, neither an estimate of the other.** Worker 3's full-tree sweep
  at the current working tree: **7 failed, 7630 passed, 40 skipped**. Worker 0's isolated
  run of the four affected modules (`tests/test_list_field.py`,
  `tests/utils/test_querysets.py`, `tests/orders/test_sets.py`,
  `examples/fakeshop/test_query/test_list_field_api.py`): **12 failed, 525 passed**. The
  gap is a selection effect, not a disagreement — state the scope with any figure quoted
  from here, and do not average or reconcile them.
- **Mechanically not ours.** None of the four failing modules contains a single
  `rest_framework` reference, so none reaches this cycle's one production edit; and every
  production module they exercise (`list_field.py`, `utils/querysets.py`, `orders/sets.py`)
  is byte-clean against `HEAD`, so for those tests the working tree **is** `HEAD`. The
  failures are red at the committed `4c483b6b`.
- **Consequence for the cycle.** A clean full-sweep is unobtainable until the maintainer
  resolves this, so `docs/builder/bld-final.md`'s final test-run gate cannot record a green
  full sweep and must record this instead. Resolution paths, unchanged from Worker 3's
  note 2: hand off to a separate session against the three modules; hold this cycle's final
  gate on unrelated work; or accept the cycle with the red rows recorded. Not decided here.
  Worth carrying: at least one failure is a camelCase-vs-snake_case spelling disagreement
  in a `ListArgumentError` message (`'orderBy' on branchesMaterialized` against a test
  expecting `branches_materialized`), which looks like a message-spelling decision rather
  than a design question.

### Summary

Slice 3's four dispatched findings are closed. `_assert_field_agreement` no longer fails
open when the validated `Meta` snapshot is absent — both incoherent spellings raise one
`ConfigurationError`, the two sibling `getattr` defaults on the same decision path are
retired, and three rows pin the rejection. The G2 "no `.only(...)`" contract has a
distinguishing assertion in each tier: emitted-SQL columns live, `select_related` /
`only_fields` off the stashed plan package-internal. The request-identity guard's tolerated
arm is pinned. The DRY import ratchet exists as an object-identity manifest of 19 bindings
plus 2 closure bodies, parametrized rather than looped, measured at `HEAD` rather than
transcribed, and now covers **both** shapes of the P2.1 promotion the spec's DoD sentence
names — the conversion half, `utils/inputs.py::FieldConversionBase`, was the over-tick and
is the pass's only change. Its failability is established by three independent instruments
and its identity by three independent measurements. No production code changed in pass 2.
Both prior escalations stand as decided; a third is opened: `HEAD` is red from the
concurrent `spec-050` work, established mechanically rather than asserted, and it neither
belongs to this slice nor blocks it.

### Spec changes made (Worker 1 only)

**None made here.** Slice 2 owns every spec and rationale rewrite and runs next. The
prior pass's list of eight is re-checked against pass 2 and stands **complete and correct
with no additions and no removals** — pass 2 changed one test file and no production or
spec surface, so nothing in it could falsify or add to a spec obligation. Restated in one
line each so Slice 2 inherits one list; the full statement of each is in
`## Final verification (Worker 1)` → `### Spec changes made (Worker 1 only)` above.

1. `## Slice checklist` → Slice 1 → `**DRY / reuse**` (spec `:640-642`) — the DoD check's
   **mechanism**: an object-identity ratchet at
   `tests/rest_framework/test_dry_import_ratchet.py`, not a grep; state the interned-`str`
   ceiling on the four kind-constant rows honestly; "why identity, not grep" to the
   rationale companion.
2. Same bullet — the DoD check's **population**, stated explicitly instead of the pronoun
   "these". Under Escalation A option (a) that is P1.4's four skeleton symbols, P2.1's
   **both** shapes (`InputFieldSpec` **and** `FieldConversionBase`), P2.2's trio, P1.3's
   cache pair, P2.3's suffix helper, the four input-kind constants, and
   `graphql_camel_name`. **Confirmed against the shipped 19-row manifest this pass** — the
   wording this item asks for and the file now agree, so Slice 2 is transcribing a measured
   population rather than proposing one.
3. Same bullet — P2.3's stale owner: `mutations/inputs.py::_pascalize_token` shipped as
   `utils/inputs.py::pascalize_token`.
4. `### Import manifest` (spec `:2582`), the `serializer_converter.py` row — stale per
   audit 1a F1 and re-measured at `HEAD`; re-file against measured bindings, including the
   six real `utils/inputs.py` imports and `utils/strings.py::pascal_case`.
5. `### Import manifest` (spec `:2583`), the `inputs.py` row — six named symbols bound in
   neither consumer module; `build_and_stash_input` lives in `rest_framework/sets.py`. The
   `resolvers.py` row (audit 1c C4) still owes Worker 1's choice among that audit's three
   resolution paths.
6. rev6 #1 — the agreement guard's meta arm must describe a **raise**, not a stop, under
   both spellings; state the snapshot requirement (`operation` **and** `optional_fields`)
   as a contract sentence; fix the citation to the non-existent
   `_assert_injected_field_agreement`.
7. Slice-3 checklist and Definition-of-done item 4 — state the G2 **tier split** (behavioral
   half live, plan-object half package-internal), citing both tests by
   `path::QualifiedName`, in agreement with `tests/rest_framework/test_resolvers.py`'s
   module docstring.
8. Edge case 7 / `## Test plan` — **no change owed**; the tolerance arm is now pinned.
   Recorded so Slice 2 does not re-raise it as a gap.

**Not spec edits. Four carries, each with a named home so none dies unowned.**

- (i) **`examples/fakeshop/apps/kanban/constants.py` goes stale the moment
  `tests/rest_framework/test_dry_import_ratchet.py` is staged.** The
  `kanban-tracked-path-constants` hook cannot see an untracked file, so a green
  `uvx pre-commit` today is `START.md`'s documented fail-open, not coverage. Owner:
  **commit time** — `uv run python scripts/build_kanban_tracked_path_constants.py` after
  `git add`, landed as a constants-only sync commit. That file is outside this cycle's fence.
- (ii) **The plan's node-id figure in this artifact is stale by one.**
  `## Plan (Worker 1)` → `### Implementation steps` → `#### Item 3 — the DRY import ratchet`,
  step 9 reads *"20 node ids total."* and step 8's Table A is 18 rows; the shipped file is
  **19 identity rows + 2 closure rows = 21 node ids**, the extra row being
  `| rest_framework/serializer_converter.py | FieldConversionBase | utils/inputs.py | P2.1 |`.
  Both Worker 2 and Worker 3 routed the correction here. **Corrected in this section rather
  than in place**: the pass sequence is append-only (`docs/builder/ARTIFACT.md`
  `## Re-pass sections`), and silently editing a plan figure after the fact hides from a
  reader that the plan and the build disagreed. This entry is the correction of record.
- (iii) **The widened docstring's ragged wrap** at
  `tests/rest_framework/test_dry_import_ratchet.py:3-8` — line 6 ends at column 55
  mid-paragraph while its neighbours run to ~85. Measured, not taken on prose. Purely
  cosmetic: `ruff format` does not reflow docstring prose, and `ruff check`,
  `ruff format --check` and `scripts/check_trailing_commas.py --check` all pass on the file,
  so no gate sees it. Worker 1 may not edit tests (`docs/builder/worker-1.md` `## Scope`)
  and Slice 2 is spec-only, so it has no owner inside the remaining slices. Owner:
  **`docs/builder/bld-final.md`'s `### Deferred work catalog`**, and folded into the diff of
  any Worker 2 pass the integration pass dispatches over this file, whichever comes first.
  It does not justify a re-loop on its own.
- (iv) **Two standing cleanup candidates in production code**, unchanged and not this
  cycle's: the `f"SerializerMutation {…}: "` message-prefix consolidation in
  `rest_framework/resolvers.py`, and audit 1a's two `rest_framework/inputs.py` duplications
  (the nested-serializer message tail, the twice-derived provisional input-type name). Each
  needs an owning card before the cycle closes; the cross-slice integration pass is where
  that is confirmed.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
