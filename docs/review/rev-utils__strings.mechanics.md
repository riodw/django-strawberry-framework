# Review · Mechanics: `django_strawberry_framework/utils/strings.py`

Status: verified
Run: 0.0.15 2026-09-24-1

## Trace

Target read whole at blob `3ec3b262`; orientation `review_inspect.py` into
`<root>/mechanics/inspect/` (leads only). Every importer and call site traced (`rg` over the
package, tests, examples): 30 production calls across `optimizer/walker.py`, `types/base.py`,
`types/finalizer.py`, `management/commands/inspect_django_type.py`, `types/converters.py`,
`rest_framework/serializer_converter.py`, `rest_framework/inputs.py`, `mutations/inputs.py`,
`forms/inputs.py`, `utils/inputs.py`, `utils/permissions.py`, `orders/sets.py`,
`sets_mixins.py`, `filters/inputs.py`. Contract sources read: `types/definition.py::DjangoTypeDefinition`
invariants, `types/relations.py::PendingRelation` docstring (states the snake-cased key),
`optimizer/walker.py::_resolve_field_map` docstring (states raw fallback keys),
`types/resolvers.py::_field_meta_for_resolver` (raw-key lookup),
`optimizer/extension.py` unregistered-target audit (iterates keys, looks hints up by them),
Django `Field._check_field_name` in `.venv` (forbids trailing `_`, `__`, `pk`; nothing about
case), Strawberry `NameConverter.get_graphql_name` / `apply_naming_config` and
`str_converters.to_camel_case` in `.venv`, `docs/README.md` quick start (optimizer is the
documented default), `docs/GLOSSARY.md` naming mentions, commit `1488e464` (the `__x` marker).
Existing fixture `tests/types/test_definition_order.py::test_camel_case_field_collision_raises`
shows the package already treats mixed-case model fields as an input shape it audits.

Workspace runs, copy `review/utils/strings.py/mechanics`, package digest
`sha256:df761b82...9f3130` (= `## Bench baseline` digest), copy `fresh`, default cell:

- `review-20260925T033713-1c7390`: probe `<root>/mechanics/test_probe_camel_field.py` (copied to
  `tests/_probe_mech/` in the copy), `pytest tests/_probe_mech/test_probe_camel_field.py --no-cov
  -n0 -s`: 2 collected, 2 executed. Prints `FIELD_MAP_KEYS ['id', 'is_public', 'name']`;
  optimizer on: `ERRORS [GraphQLError('An unexpected error occurred.' ...)] DATA None`;
  optimizer off (positive control): `DATA {'things': [{'id': 1, 'name': 'a', 'isPublic': True}]}`,
  one query selecting `"isPublic"`.
- `review-20260925T033732-7993c9`: same node `[True]` w/ `-o log_cli=true --log-cli-level=ERROR`:
  the error-policy log carries `django.core.exceptions.FieldDoesNotExist: _CamelThing has no
  field named 'is_public'` raised from `QuerySet.only` select-mask resolution.
- `review-20260925T033937-78b854`: `snake_case` is the identity on 20,000 random
  `[a-z0-9_]` names (the "Must not change" row below); `snake_case.__doc__` at runtime is
  `_snake_case_cached`'s first line.

Cells: the target itself reaches no database, alias or dialect decision; M1's failure is in
`QuerySet.only` field resolution, which is model metadata, dialect-independent. Sharded and pg
`inapplicable by construction` for the finding; the verifier judges.

Fingerprints (`git hash-object`, 12 chars): `utils/strings.py` 3ec3b262ea86; `types/base.py`
91c587477ff8; `types/finalizer.py` 77fd9a2dd229; `types/relations.py` 6bd7c63da778;
`types/definition.py` fa6c4d330e72; `types/resolvers.py` 72d62dc4ebfe; `optimizer/walker.py`
611e8fae4985; `optimizer/extension.py` e0e53a8e10fc; `optimizer/nested_planner.py`
b4dfd4a6f610; `management/commands/inspect_django_type.py` 46dffb3db4dc; `utils/inputs.py`
ee31d360c1db; `utils/__init__.py` 1a4c2ec8bfd3; `exceptions.py` e06b0b7f776e;
`mutations/inputs.py` fc4420475f40; `sets_mixins.py` ad8987ea2fb1; `filters/inputs.py`
82b52d97b8f8; `types/converters.py` 058f10813927; `rest_framework/serializer_converter.py`
6652d092544e; `tests/utils/test_strings.py` 3dad1a9d42d8; `tests/types/test_definition_order.py`
aa9435fd27ad; `tests/optimizer/test_walker.py` 41256c14e13e;
`examples/fakeshop/apps/kanban/schema.py` fd432eb32de3.

## Findings

### High

#### M1: `snake_case` keys `DjangoTypeDefinition.field_map`, so a mixed-case model field crashes every optimized query that selects it

- **Contract row** — `DjangoTypeDefinition.field_map` maps a selected Django field to its
  `FieldMeta` by that field's name: the walker fallback builds it `{f.name: ...}`
  (`django_strawberry_framework/optimizer/walker.py::_resolve_field_map`),
  `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` and
  `django_strawberry_framework/optimizer/nested_planner.py` look it up by raw Django name, and
  the optimizer turns a hit's key into the `.only()` column. Django permits any field name bar a
  trailing `_`, `__` and `pk` (`Field._check_field_name`); the package does not refuse mixed case
  and its field-surface audit handles it (`test_camel_case_field_collision_raises`).
- **Observation** — `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`
  builds the canonical map as `{snake_case(f.name): ...}`. `snake_case` reverses a GraphQL
  camelCase name; applied to a Django name it is the identity only while the name has no
  uppercase letter. For `isPublic` the key becomes `is_public`, and
  `django_strawberry_framework/optimizer/walker.py::_resolve_selection_target` reverses the
  selection `isPublic` to the same `is_public`, hits, and returns it as the Django name, so the
  plan projects `.only("is_public")`. Five readers re-apply `snake_case` to a Django name to find
  the entry (`django_strawberry_framework/types/base.py::_validate_relation_shape_targets`,
  `django_strawberry_framework/types/base.py::_build_annotations`, `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`, `django_strawberry_framework/types/finalizer.py::finalize_django_types`,
  `django_strawberry_framework/management/commands/inspect_django_type.py::Command._resolve_row`);
  `types/relations.py::PendingRelation` documents the snake key. The raw-key readers
  (`_field_meta_for_resolver`, the extension's hint lookup `hints.get(field_name)`) silently miss
  on the same names. One map, two key rules.
- **Evidence** — HUNT record: run `review-20260925T033713-1c7390` (copy
  `review/utils/strings.py/mechanics`, package `__file__` inside the copy per the header, digest
  `sha256:df761b82...9f3130`, database `NAME` the copy's own `db.sqlite3` test database),
  command `pytest tests/_probe_mech/test_probe_camel_field.py --no-cov -n0 -s`, 2 collected / 2
  executed. Project shape: `managed=False` model `_CamelThing(isPublic=BooleanField, name=TextField)`
  under `app_label="products"`, `DjangoType` w/ `fields=("id", "name", "isPublic")`,
  `DjangoListField`, `DjangoSchema(..., extensions=[lambda: opt])` exactly as `docs/README.md`
  quick start. Reach assertion: `FIELD_MAP_KEYS ['id', 'is_public', 'name']`. Wire input
  `{ things { id name isPublic } }`. Result: masked internal error;
  `review-20260925T033732-7993c9` shows `FieldDoesNotExist: _CamelThing has no field named
  'is_public'`. Positive control: the same schema w/o the optimizer returns the row.
- **Impact** — every query selecting a mixed-case scalar (or relation, through the same key)
  on an optimized schema fails with an internal error; the unoptimized path serves it. The
  raw-key readers mis-resolve the same fields silently (resolver `FieldMeta` fallback, an
  `OptimizerHint.SKIP` on a mixed-case relation ignored by the unregistered-target audit).
- **Severity** — High: public-contract correctness failure on the documented default schema
  shape. Factor that bounds it: reach needs a mixed-case model field (legal Django, discouraged
  by PEP 8 / N815); the failure is loud, no data exposure.
- **Recommendation** — owner `types/base.py::DjangoType.__init_subclass__`: key the map by the
  raw Django name, `{f.name: FieldMeta.from_django_field(f) for f in fields}`, and drop
  `snake_case` from the five Django-name lookups above (each becomes `field_map[<name>]`),
  removing the then-unused `snake_case` imports in `types/base.py`, `types/finalizer.py`,
  `inspect_django_type.py`. The walker keeps its three `snake_case(sel.name)` calls (they reverse
  GraphQL selection names, the helper's real contract); on a miss its existing forward resolver
  `optimizer/walker.py::_field_by_graphql_name` matches `isPublic` against the Strawberry field
  name and returns the real `field.name`, so no walker change is needed. Update the docstrings
  that state the snake key (`types/relations.py::PendingRelation`, the "already snake_cases the
  lookup side" sentence in `optimizer/walker.py::_resolve_field_map`) and the test-local map
  builders that copy the old rule (`tests/optimizer/test_walker.py` three sites,
  `tests/optimizer/test_multi_db.py`, `tests/types/test_relay_interfaces.py`; identical output
  for their lowercase fields). Permanent test at the package tier: no fakeshop model carries a
  mixed-case field and an item adds no example model, so Worker-2 names that fixture gap for
  `## Decisions`. Ungated `#"substring"` citers quoting the edited lines live only in archived
  history (`docs/SPECS/spec-016-...`, `docs/SPECS/spec-010-...`, `docs/SPECS/appx/spec-004|010|016-...`,
  `docs/builder/DONE/build-004|010|016-...`): records of their date, not rewritten.
  `examples/fakeshop/apps/kanban/schema.py` cites `_walk_selections #"snake_case(sel.name), None"`,
  a line this fix leaves alone.
- **Must not change** — every map key for a lowercase field name (the identity shown in
  `review-20260925T033937-78b854`), so every existing plan, query count and schema is
  byte-identical on fakeshop; `test_camel_case_field_collision_raises` still raises at finalize;
  the walker's digit-boundary forward resolution (`address_2` / `isbn13` tests in
  `tests/optimizer/test_walker.py`) unchanged.
- **Proof** — at `review/utils/strings.py/verify-mechanics-<n>`:
  (1) `workspace.py run <address> -- pytest <node> --no-cov` passes, where `<node>` is the test
  Worker-2 names (default: a new test `test_mixed_case_model_field_selection_projects_its_real_column` in
  `tests/optimizer/test_extension.py`; it does not exist before the fix)
  and it asserts, on a synthetic `managed=False` model w/ `isPublic = BooleanField()` under
  `DjangoOptimizerExtension`: `sorted(definition.field_map) == sorted(f.name for f in definition.selected_fields)`,
  `result.errors is None`, data `[{"id": <pk>, "name": "a", "isPublic": True}]`, exactly 1 query,
  whose SQL contains `"isPublic"`;
  (2) `workspace.py prove <address> <root>/verify-mechanics-<n>/m1.json` w/ `reverse_patch` = the
  `types/base.py` hunk, `expect_failing` = [`<node>`]: the node fails w/o the change;
  (3) `rg -n "snake_case\(" django_strawberry_framework/types django_strawberry_framework/management`
  prints 0 lines (before: 7, incl. the `relations.py` docstring), and
  `rg -c "snake_case\(sel\.name\)|snake_case\(graphql_name\)" django_strawberry_framework/optimizer/walker.py`
  prints 3 (unchanged);
  (4) `workspace.py run <address> -- pytest tests/types/test_definition_order.py::test_camel_case_field_collision_raises tests/optimizer/test_walker.py tests/optimizer/test_multi_db.py tests/types/test_relay_interfaces.py tests/types/test_finalizer.py --no-cov`
  passes.
- **Freshness** — `types/base.py` 91c587477ff8; `optimizer/walker.py` 611e8fae4985;
  `types/finalizer.py` 77fd9a2dd229; `types/relations.py` 6bd7c63da778; `types/resolvers.py`
  72d62dc4ebfe; `optimizer/extension.py` e0e53a8e10fc; `inspect_django_type.py` 46dffb3db4dc;
  `utils/strings.py` 3ec3b262ea86.

### Medium

None.

### Low

None.

## Rejected

- **Generated input field names ignore `auto_camel_case=False` / a custom `NameConverter`.**
  `django_strawberry_framework/utils/inputs.py` pins every generated filter / order / mutation
  input field w/ `name=graphql_camel_name(python_attr)`, and Strawberry's
  `NameConverter.get_graphql_name` returns a pinned name before applying the naming config, so
  under `auto_camel_case=False` output fields are snake_case while generated input fields stay
  camelCase. No contract source says generated inputs follow the naming config
  (`docs/README.md` states it only for list arguments; `docs/GLOSSARY.md` only forwards the
  kwarg), so not a defect. Reopens if a doc or card states that input field names follow the
  schema's naming config; Worker-0 may list it under `## Decisions`.
- **`graphql_camel_name` beside Strawberry's `to_camel_case` as two camelizers.** Change
  challenge "change how a Django name maps to a GraphQL field name": one package-owned definition
  (`graphql_camel_name`, injective, for names the package pins) and one upstream one
  (`to_camel_case` via the schema `NameConverter`, for output fields). Different contracts, the
  separation recorded at `django_strawberry_framework/mutations/inputs.py` (the `to_camel_case`
  fallback docstring). Reopens if the package pins output field names too.
- **`snake_case`'s `__x` marker branch has no production feeder.** No caller passes
  `graphql_camel_name` output to `snake_case` (the walker reverses Strawberry output names, which
  never contain `__x`; after M1 nothing else calls it), so the branch serves only the round-trip
  property `tests/utils/test_strings.py::test_graphql_camel_name_round_trips_normalized_snake_case`.
  The maintainer committed it as a contract (`1488e464`); cold, bounded. Reopens if the
  round-trip claim is dropped, or a caller starts reversing pinned input names.
- **`pascal_case` (no guard) at the two enum-name sites vs `pascal_case_or_raise` at the two
  set-naming sites.** `types/converters.py` and `rest_framework/serializer_converter.py` build
  `<Type><Field>Enum` from a model / serializer field name; `pascal_case` returns `""` only for an
  all-underscore name, which Django's E001 check forbids on a model field. No contract makes the
  guard apply there. Reopens on a supported input yielding an all-underscore choice field name.
- **`pascal_case` interior `__` collapse beside `flatten_lookup_path`.** One makes a type-name
  stem, the other a Python attribute / alias; different outputs, reasons to change and owners
  (`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` relies on the collapse).
  Reopens if both must change together for one `LOOKUP_SEP` rule change.

Looks-for discharged, `none`: rule at a caller instead of its owner (the empty-stem guard lives in
`pascal_case_or_raise`; `filters/inputs.py::_pascal_case` supplies only its error); policy in an
adapter / mechanism in a policy layer (pure mechanism module); mode flag (none); state owned in
two places (M1 is the one case, at the caller); dependency direction (`utils/strings.py` imports
only stdlib and `exceptions.py`, which imports nothing first-party; no `TYPE_CHECKING`);
`django.conf.settings` at import (none); `__all__` (five names, all defined, `utils/__init__.py`
re-exports `pascal_case` / `snake_case` only, `utils/inputs.py` re-exports `graphql_camel_name`
for its consumers); sync/async twins (none); `snake_case.cache_*` grafts used only by
`tests/utils/test_strings.py`, kept for the cache-behavior pin; branch no real path reaches
beyond the `__x` rejection (`_plain_text`'s subclass branch is reached by Django `SafeString`
and other `str` subclasses in configuration).

## Cross-axis (from mechanics)

Placed in `rev-utils__strings.comments.md` `## Cross-axis (from mechanics)` once that record
existed: F1's proposed module text must not say the `DjangoType` field maps key on `snake_case`
after M1, and M1 makes the snake-key sentences in `types/relations.py::PendingRelation` and
`optimizer/walker.py::_resolve_field_map` stale. The `pascal_case` "cannot contain upper-case"
claim and the `functools.wraps` dead docstring are already Comments F4 and F2.

## Cross-axis (from performance)

None at close.

## Cross-axis (from Comments)

Reconstructed by this pass: the Comments record's `Handoff:` says two leads were placed here, but
the section was absent when this record closed (this pass rewrote the record wholesale after
creating its skeleton, which most likely dropped the append). Restated from that `Handoff:`;
the Comments owner should confirm the wording. Graded now, re-graded at verification.

- **`_plain_text` twins.** `django_strawberry_framework/utils/strings.py::_plain_text` rejects a
  non-string w/ `ConfigurationError`; `django_strawberry_framework/utils/imports.py::_plain_text`
  passes it through to the import machinery. Change challenge "change how a `str` subclass is
  copied to an exact `str`": both bodies change, but the shared part is the one expression
  `str.__str__(value)`; the non-string halves differ by contract, each pinned by its own tests.
  Disposition: rejected here, no consolidation: one expression is not a rule w/ its own reasons
  to change, and sharing it would add a `utils/imports.py` -> `utils/strings.py` edge for it.
  Reopens if the normalization grows a second step or a third copy appears; the `utils/`
  integration item's Mechanics pass ("a rule split across siblings") is the named owner.
- **Letter-case collision** (`my_HTTP` / `my_http`, both legal Django names, share `MyHttp` from
  `pascal_case` and `myHttp` from `graphql_camel_name`). No contract promises case-injectivity.
  By reading: both exposed as output fields collide under `to_camel_case` too and the
  field-surface audit raises at finalize (`test_camel_case_field_collision_raises` shape);
  generated inputs over both raise at the duplicate-GraphQL-name check in
  `django_strawberry_framework/utils/inputs.py` before any class registers. Disposition:
  rejected as a robustness row, not a defect. Reopens on a supported shape where only a
  `pascal_case` type-name stem collides (no field-name collision to fail first) and Strawberry
  silently keeps one type.

Handoff: Read beyond the trace: Strawberry's `NameConverter` / `to_camel_case`, Django's field-name
check, the walker's `_walk_selections` fallback and `_selected_scalar_names` region, the
existing `fooBar` collision fixtures (`tests/types/test_definition_order.py`,
`tests/mutations/test_inputs.py`). M1's defect is at the caller of the target, not in
`strings.py`; `strings.py` itself carries no Mechanics change. The verifier should attack M1 with
a mixed-case forward FK (`select_related` path) and a mixed-case many-side relation (prefetch
and `relation_shapes`), and run the async flavor, since all share the walker's key. Worker-2's
walker needs no edit if keys are raw: a snake hit then implies `snake == field.name`. Probe
source kept at `docs/review/temp-tests/utils__strings/mechanics/test_probe_camel_field.py`; the
copy holds a copy under `tests/_probe_mech/`. This pass rewrote its record after the Comments reviewer had
appended to it; `## Cross-axis (from Comments)` is reconstructed from that reviewer's `Handoff:`.

## Verification (Mechanics)

Verify pass 1, address `review/utils/strings.py/verify-mechanics-1`, copy synced fresh from the
shared tree, package digest `sha256:a7408aee...c703e8` (= Worker-2's "after" digest). Item diff
`docs/review/temp-tests/utils__strings/diff/pass-1.diff` (blob `b8c938472fac`, 12 paths). Proof
lines run before reading `## Implementation (Worker-2)`.

Proof results (M1):

1. `review-20260925T035700-1954d2`: `pytest tests/optimizer/test_extension.py::test_mixed_case_model_field_selection_projects_its_real_column
   tests/optimizer/test_extension.py::test_mixed_case_relation_selections_plan_through_their_django_names --no-cov -n0`:
   2 passed. Read the node body: it asserts every clause of the Proof (no errors, the exact data
   row, exactly 1 query, SQL carries `"isPublic"`, `sorted(field_map) == sorted(selected names)`).
   Landed.
2. `workspace.py prove`, manifest `<root>/verify-mechanics-1/m1.json` (reverse_patch = the item
   diff, `target` = `types/base.py`, scope both new nodes + `--show-capture=no`), run
   `review-20260925T035725-6ced70`: unmutated 2 passed; mutated blob `91c587477ff8` (= HEAD blob),
   **pinned**, the 2 failing rows are exactly `expect_failing` (scalar node: masked
   `GraphQLError`; relation node: `ConfigurationError ... pending relation petItems has invalid
   field metadata. KeyError` at finalize, since the base.py-only revert leaves finalizer raw);
   restore byte-proved (`49057fad2058`). Landed.
3. `rg -n "snake_case\(" django_strawberry_framework/types django_strawberry_framework/management`:
   0 lines (HEAD: 7 via `git grep`); walker `snake_case(sel.name)|snake_case(graphql_name)` count 3,
   HEAD 3. Landed.
4. `review-20260925T035742-cc1de2`: the Proof's five-target scope, 349 passed. Landed.

Worker-2's numbers reproduced: Proof (4) + the two new nodes = 349 + 2 = 351 (its
`review-20260925T035353-5891aa`); whole default suite in my copy `review-20260925T035756-5cc710`:
8852 passed, 40 skipped, 2 failed, the two `tests/test_ci_governance.py` git-index tests
(`git ls-files` exit 128, no `.git` in a copy; environmental, the gate copy carries an index),
identical to its `review-20260925T035001-6271cb`. Its M1 failability (`review-20260925T035329-f06d73`,
pinned, 2 rows) matches my run 2.

Whole-diff reading through Mechanics:

- Code hunks are exactly M1's owner change (`DjangoType.__init_subclass__` key) plus the five
  Django-name readers and three import removals, and the test-local map builders; every
  `field_map[...]` / `.field_map.get(...)` reader in the package now indexes by the Django name
  (`types/resolvers.py::_field_meta_for_resolver`, `optimizer/nested_planner.py`, the extension's
  hint lookup were already raw); the walker alone applies `snake_case`, to GraphQL selection names,
  each with the forward fallback (`_resolve_selection_target`, `_walk_selections`' unresolved
  branch, the FK-id-elision helper's `_field_by_graphql_name` miss path).
- `types/finalizer.py::finalize_django_types`: a malformed pending name now raises `KeyError`
  instead of `snake_case`'s `ConfigurationError`/`AttributeError`; the existing `except
  BaseException` wraps it into the same `ConfigurationError`, and
  `tests/types/test_finalizer.py::test_malformed_pending_field_name_is_rejected_before_relation_lookup`
  passes in run 4 (behavior preserved, docstring updated).
- `utils/strings.py` code: `_plain_text` reorder is behavior-identical (`type(v) is str` implies
  `isinstance(v, str)`); `functools.wraps` dropping `"__doc__"` changes only `snake_case.__doc__`.
  Worker-2's `expect_failing: []` revert of `strings.py` covers both.
- Test tier: package tier is the strongest existing one; `rg` over `examples/fakeshop/apps` finds
  no mixed-case model field or `related_name`, so the fixture gap in the plan's `## Decisions` is
  real.
- Lint gates on the 12 touched paths, `--check` forms: `ruff check` passed; `ruff format --check`
  12 already formatted; `check_trailing_commas.py --check` 0 violations; `check_citations.py
  --check` 1280 resolve. No symbol was renamed or moved, so no `--cited-by` population; ungated
  `#"substring"` quoters of the edited lines sit only in `docs/SPECS/` and `docs/builder/DONE/`
  archives (6 files), as the record stated.

Attacks (probe source `<root>/verify-mechanics-1/test_probe_vm1.py`, run from
`tests/optimizer/test_probe_vm1.py` in the copy), `review-20260925T040047-726760`, 4 passed:
async flavor (`await schema.execute`, mixed-case scalar + reverse FK prefetch + nested forward FK),
`relation_shapes = {"petItems": "connection"}` on Relay types (`petItemsConnection`, 2 queries at
1 and 3 owners), `OptimizerHint.SKIP` on mixed-case `ownerRef` with the target unregistered
(`check_schema` warnings `[]`), and `inspect_django_type` on a mixed-case type. Pre-fix was the
worse behavior: `prove` manifest `<root>/verify-mechanics-1/attack.json` reverting the three code
files to their HEAD blobs, run `review-20260925T040102-51c678`, **pinned**: async and connection
rows fail with the masked internal error, the SKIP row fails (audit warns on the hinted relation);
the inspect row passes both ways (its reader and the map shared the snake key before). No new
problem; these shapes consume the same key the permanent tests' `field_map` assertion pins, so no
further permanent test is owed.

Cells: sharded and pg `inapplicable by construction` holds: the change is model-metadata name
resolution before any SQL is built; the failing pre-fix calls (`QuerySet.only`, `select_related`,
finalize lookup) raise before a connection is chosen.

Disputes: none recorded by Worker-2 on Mechanics. Cross-axis (from Comments) rejections unchanged:
the diff touches neither `utils/imports.py` nor any name-collision path.

Named gap for Worker-0 to route (Comments axis, not in the item diff):
`django_strawberry_framework/optimizer/field_meta.py::FieldMeta.from_django_field` documents
`name` as "The Django field name (snake_case)"; after M1 the field map is keyed by that raw name,
which may be mixed case (`isPublic`). A one-word docstring fix at the owner; Comments grades
whether it rides on this item.

Fingerprints (12 chars), all equal to Worker-2's: `utils/strings.py` 536d175cd605; `types/base.py`
49057fad2058; `types/finalizer.py` de34ae2aaed1; `types/relations.py` 4098eebca9b9;
`types/__init__.py` 1bf69028dbdc; `optimizer/walker.py` 73d6929a5881;
`inspect_django_type.py` 2807d0fc9d75; `tests/optimizer/test_extension.py` 4101bbd3805e;
`tests/optimizer/test_walker.py` 7a76159a24f6; `tests/optimizer/test_multi_db.py` 16753577c693;
`tests/types/test_finalizer.py` 05e1c9ecf621; `tests/types/test_relay_interfaces.py` bea2afd41616.
Read unchanged: `optimizer/field_meta.py` 7215c887aa26, `optimizer/extension.py` e0e53a8e10fc,
`types/resolvers.py` 72d62dc4ebfe, `optimizer/nested_planner.py` b4dfd4a6f610.

Verdict: verified.

Handoff: Read beyond the record: the walker's three `snake_case` sites and their forward
fallbacks, every package `field_map` reader, `prove_failability.py`'s manifest format (`sites`
with per-target `reverse_patch` against one diff file works). The attack probe lives only in my
copy and `<root>/verify-mechanics-1/`; it is not a permanent test. Open: the `FieldMeta` docstring
gap above; the plan's fixture decision (a fakeshop mixed-case model) would let both new nodes and
the async/connection/SKIP shapes move live. `--show-capture=no` was needed in both manifests.
