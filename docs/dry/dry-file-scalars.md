# DRY review: `django_strawberry_framework/scalars.py`

Status: verified

## System trace

`scalars.py` owns two things: the package-custom `BigInt` scalar (strict
`_parse_bigint` / `_serialize_bigint`, registered in `_PACKAGE_SCALAR_MAP`) and
the `strawberry_config()` factory that builds a `StrawberryConfig` carrying
`_PACKAGE_SCALAR_MAP` merged with a consumer's `extra_scalar_map`. `Upload` /
`UploadDefinition` are re-exported from Strawberry's own
`strawberry.file_uploads.scalars` verbatim - deliberately NOT added to
`_PACKAGE_SCALAR_MAP` since `DEFAULT_SCALAR_REGISTRY` already owns it.

Traced every importer of `django_strawberry_framework.scalars` / re-exports of
`BigInt`, `Upload`, `strawberry_config`:

- `strawberry_config()` is the sole production call site building a
  `StrawberryConfig` with `scalar_map=` anywhere in the package or the example
  project (`rg StrawberryConfig\(` outside `scalars.py` only matches one test
  that deliberately uses plain `StrawberryConfig()` to prove `Upload` resolves
  without the package helper, per Decision 5). No parallel config-building path
  exists to consolidate.
- `types/converters.py::SCALAR_MAP` maps `models.BigIntegerField` /
  `models.PositiveBigIntegerField` -> `BigInt` (the NewType, not the
  `ScalarDefinition`). This is a distinct responsibility - Django-field-class ->
  GraphQL-scalar-type for auto field conversion - not the schema-level scalar
  registration `_PACKAGE_SCALAR_MAP` performs. Both must reference `BigInt`;
  neither duplicates the other's rule.
- `mutations/inputs.py`, `forms/inputs.py`, `rest_framework/serializer_converter.py`
  each import `Upload` and assign `annotation = Upload` for a `FILE`-kind column
  in their own independent input-building pipeline. The shared classification
  (`FILE` kind) already has one owner (`utils/inputs.py`); the one-line
  terminal assignment differs per pipeline only because each of the three
  mutation flavors (model / form / DRF serializer) builds a structurally
  different Input shape by design (AGENTS.md's DRF-first, three-flavor
  architecture). Rejected as a consolidation target - see Verification.
- `management/commands/inspect_django_type.py` imported `BigInt` for exactly one
  purpose: a hardcoded `BigInt: "BigInt"` entry in its own
  `_GRAPHQL_SCALAR_NAMES` fallback table, used only when the command runs
  without `--schema` (no live schema `scalar_map` to consult). This duplicated,
  as a second literal, the scalar's public GraphQL name that `scalars.py`
  already declares once via `strawberry.scalar(name="BigInt", ...)`. See
  Opportunities.

## Verification

- `rg` for `StrawberryConfig\(` confirms `strawberry_config()` has no
  competing config-building call site in production code.
- `rg` for `re\.compile\(r"\^"` confirms `_BIGINT_STRING_PATTERN` (the strict
  decimal-string grammar) has no sibling regex anywhere else in the package -
  the strict parse/serialize contract is genuinely singular.
- Considered treating the three `annotation = Upload` sites
  (`mutations/inputs.py`, `forms/inputs.py`, `rest_framework/serializer_converter.py`)
  as duplication. Rejected: each pipeline already delegates the *shared* fact
  (which columns are file-kind) to one owner, `utils/inputs.py::FILE`; the
  remaining code per site is a single-line terminal mapping inside an
  otherwise-independent Input-shape builder that intentionally differs by
  mutation flavor. Collapsing these into a shared helper would either add a
  mode-flag-shaped indirection or couple three independently-evolving builders
  for a one-line saving - against DRY.md's explicit guidance not to optimize
  for fewer lines at the cost of a convenience helper that obscures ownership.
- Ran the two `inspect_django_type` test suites
  (`tests/management/test_inspect_django_type.py`,
  `examples/fakeshop/tests/test_inspect_django_type.py`) with
  `--cov=django_strawberry_framework.management.commands.inspect_django_type
  --cov-report=term-missing` against the pre-edit source: the file already
  reported 100% line coverage. Inspection showed why the `BigInt: "BigInt"`
  entry was "covered" despite no test ever exercising the fallback lookup for
  `BigInt` specifically - the line executes at import time as part of building
  the module-level dict literal, regardless of whether `.get(BigInt)` is ever
  called at runtime. No existing test called `inspect_django_type` (bare name
  or dotted path, no `--schema`) against a type with a `BigIntegerField` /
  `PositiveBigIntegerField` column, so the actual behavior this entry exists
  for was untested - a real drift risk hiding behind a green coverage report.

## Opportunities

**Repeated responsibility:** the public GraphQL name of the package's
`BigInt` scalar.

**Sites:**
- `django_strawberry_framework/scalars.py::_BIGINT_SCALAR_DEFINITION` -
  `strawberry.scalar(name="BigInt", serialize=_serialize_bigint,
  parse_value=_parse_bigint)` - the authoritative declaration.
- `django_strawberry_framework/management/commands/inspect_django_type.py::_GRAPHQL_SCALAR_NAMES`
  - previously a second, independent `BigInt: "BigInt"` literal, used only as
    the cold-path (no `--schema`) fallback name in `_scalar_name()`.

**Evidence:** both sites encode the identical fact - "the SDL name of the
package's `BigInt` scalar is `BigInt`" - and must change together. If the
scalar were ever renamed in `scalars.py` (e.g. `strawberry.scalar(name=...)`
changed), nothing forced the diagnostic command's hardcoded copy to follow;
the cold-path table would keep printing the stale name for any
`BigIntegerField` / `PositiveBigIntegerField` column, and - as the coverage
check above proved - no test would catch it, since the dict-literal line
executes (and is "covered") at import time independent of whether the
specific key is ever looked up.

**Owner:** `django_strawberry_framework/scalars.py::_PACKAGE_SCALAR_MAP` -
already the single canonical registry of package-scalar -> `ScalarDefinition`
that `strawberry_config()` reads from; it is the natural root for "what is
this package scalar's public name."

**Consolidation:** `inspect_django_type.py` now imports `_PACKAGE_SCALAR_MAP`
instead of `BigInt` directly and merges `{scalar: definition.name for scalar,
definition in _PACKAGE_SCALAR_MAP.items()}` into `_GRAPHQL_SCALAR_NAMES`,
replacing the hardcoded `BigInt: "BigInt"` entry. The true GraphQL built-ins
(`int -> "Int"`, `str -> "String"`, etc.) stay hardcoded - those are fixed
GraphQL-spec constants with no in-repo owner to consolidate against, unlike
`BigInt`'s name. Any future scalar added to `_PACKAGE_SCALAR_MAP` now gets a
correct cold-path fallback name for free, with no third hand-maintained copy
needed in this command.

**Proof:** added
`examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_bigint_field_rows_use_package_scalar_name`,
which calls `inspect_django_type ScalarSpecimenType` (bare name, no
`--schema`, i.e. `scalar_map=None`) against the real fakeshop
`ScalarSpecimen` model's `signed_big` (`BigIntegerField`) and `unsigned_big`
(`PositiveBigIntegerField`) columns and asserts both rows report `BigInt!`.
This exercises the exact branch the old hardcoded literal only appeared to
cover; it now proves the fallback name is actually derived from
`scalars.py`'s live `ScalarDefinition`, not an independent copy. Full targeted
run: `tests/management/test_inspect_django_type.py`,
`examples/fakeshop/tests/test_inspect_django_type.py`, `tests/test_scalars.py`
- 85 passed.

**Risks / non-goals:** the true GraphQL built-in name constants
(`int`/`str`/`bool`/`float`/`Decimal`/`UUID`/date-time family/`JSON`) are
intentionally left as hardcoded literals - they are fixed by the GraphQL spec
/ Strawberry itself, not by anything this package owns, so there is no
in-repo single source of truth to point them at. `_PACKAGE_SCALAR_MAP` stays
private (no new public export); `inspect_django_type.py` already imports
other underscore-prefixed package internals across module boundaries
(established convention, e.g. `optimizer/extension.py` importing
`nested_fetch._active_strategy`), so importing `_PACKAGE_SCALAR_MAP` follows
existing precedent rather than introducing a new one.

## Judgment

`scalars.py` itself needed no change - `strawberry_config()` and the `BigInt`
parse/serialize pair are each singular, with no competing implementation
anywhere in the package or example project. The one real duplication was a
connected file's hardcoded second copy of the scalar's authoritative name,
now removed in favor of deriving it from `scalars.py`'s own scalar map. The
Upload-annotation three-site pattern was traced and deliberately rejected as
already-DRY at the level that matters (shared `FILE` kind classification;
divergent per-mutation-flavor Input construction by design).

## Implementation (Worker 1)

- **Owner chosen:** `django_strawberry_framework/scalars.py::_PACKAGE_SCALAR_MAP`
  (pre-existing; no new symbol added).
- **Migrated:**
  `django_strawberry_framework/management/commands/inspect_django_type.py` -
  swapped the `BigInt` import for `_PACKAGE_SCALAR_MAP` and rebuilt
  `_GRAPHQL_SCALAR_NAMES`'s package-scalar entries from it instead of a
  hardcoded literal.
- **Test added:**
  `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_bigint_field_rows_use_package_scalar_name`
  (in-process command test against the real `ScalarSpecimen` model, per
  AGENTS.md's test-placement rule - a management command is not reachable
  over `/graphql/`, so the example in-process tier is its home, exactly as
  this test file's own module docstring already documents for every other
  case here).
- **Behavior kept separate:** the true GraphQL built-in scalar names
  (`Int`/`String`/`Boolean`/`Float`/`Decimal`/`UUID`/`Date`/`DateTime`/`Time`/`JSON`)
  remain hardcoded; only the package-defined-scalar portion of the table is
  now derived.
- **Validation:** targeted run of
  `tests/management/test_inspect_django_type.py`,
  `examples/fakeshop/tests/test_inspect_django_type.py`, `tests/test_scalars.py`
  - 85 passed. `uv run ruff format .` and `uv run ruff check --fix .` clean on
  both edited files; `scripts/check_trailing_commas.py` reports no fixes
  needed.
- **Evidence for rejected findings:** see Verification above (Upload
  three-site pattern; no competing `StrawberryConfig(scalar_map=...)` builder;
  no sibling `_BIGINT_STRING_PATTERN`-shaped regex).
- **Changelog:** not touched: no maintainer authorization was sought or given
  for a `CHANGELOG.md` entry.
- Note for Worker 0 / maintainer: `django_strawberry_framework/management/commands/inspect_django_type.py`
  was already dirty at task start with unrelated concurrent work (bare-name
  resolution now also matches `definition.graphql_type_name`, and
  `_print_table`'s title uses the SDL name). That work was preserved untouched;
  this review's edit only touches the `_GRAPHQL_SCALAR_NAMES` table and its
  import line, a disjoint section of the same file.

## Independent verification (Worker 2)

Re-traced independently rather than reviewing only the edited lines.

- **Scope of the diff.** `git diff daaa5ff4f885a339a4e5594fcf68d3c43cfb75d7 --
  scalars.py inspect_django_type.py test_inspect_django_type.py` shows exactly
  two hunks: the `BigInt` import swapped for `_PACKAGE_SCALAR_MAP` and the
  `_GRAPHQL_SCALAR_NAMES` dict-literal entry replaced by a comprehension over
  it, plus one new test. `scalars.py` itself has zero diff, confirming the
  "zero-edit locally" claim.
- **Same-responsibility challenge.** Ran `strawberry.scalar(name="BigInt",
  ...)` directly: it returns a `ScalarDefinition` whose `.name == "BigInt"` -
  the exact string the old hardcoded `BigInt: "BigInt"` literal encoded. Both
  sites genuinely stated "the SDL name of the package's `BigInt` scalar is
  `BigInt`"; the consolidation target was real, not a superficial rename.
- **Migration + proof test.** Confirmed `signed_big` (`BigIntegerField`) and
  `unsigned_big` (`PositiveBigIntegerField`) are both selected fields on the
  real `ScalarSpecimenType` (`examples/fakeshop/apps/scalars/schema.py`), and
  traced `handle()` -> `scalar_namer` -> `_scalar_name`: with no `--schema`,
  `config` is `None`, so `scalar_map` is `None` and the cold-path
  `_GRAPHQL_SCALAR_NAMES.get(scalar)` branch is the one actually exercised for
  both columns - not short-circuited by a live schema `scalar_map`. Ran the
  three targeted suites named in the artifact
  (`tests/management/test_inspect_django_type.py`,
  `examples/fakeshop/tests/test_inspect_django_type.py`,
  `tests/test_scalars.py`): 85 passed, matching the claimed count.
  `--cov` on the two touched files: `scalars.py` 100%, `inspect_django_type.py`
  99% (one pre-existing, unrelated miss - see below). Wrote a scratch
  experiment (`docs/dry/temp-tests/worker2-scalars/scratch_drift.py`, run and
  removed) that mutates `scalars.py`'s live `_PACKAGE_SCALAR_MAP` entry to a
  renamed `ScalarDefinition` and re-evaluates the exact dict-comprehension the
  fix introduced: the derived name followed the rename, proving the new table
  is genuinely read from `scalars.py`'s live definition rather than a second
  frozen literal that happens to currently agree.
- **Rejected Upload-annotation sites challenge.** Read all three `annotation =
  Upload` sites in full context
  (`mutations/inputs.py:569`, `forms/inputs.py:410,423`,
  `rest_framework/serializer_converter.py:898,913`). Each sits inside a
  structurally distinct triple/annotation builder keyed off a different input
  source (Django model field, Django form field, DRF serializer field) that
  independently computes `python_attr` / `graphql_name` / `kind` alongside the
  one-line `annotation = Upload`; `forms/inputs.py` even has two independent
  occurrences (column-backed vs column-less branches) that would still need
  their own surrounding logic if extracted. Agree with the rejection: the
  shared fact (file-kind classification) already has one owner
  (`utils/inputs.py::FILE`); collapsing the terminal assignment further would
  couple three by-design-independent pipelines per AGENTS.md's DRF-first,
  three-flavor architecture for a one-line saving.
- **Missed-opportunity search.** `rg '"BigInt"' django_strawberry_framework`
  finds no other production hardcoded copy (remaining hits are the `NewType`
  name, the `__all__` entry, and a code comment). `rg` for
  `_GRAPHQL_SCALAR_NAMES` / `scalar_name` across the package surfaces no
  sibling scalar-name registry; `rest_framework/serializer_converter.py`'s
  `_scalar_name` is an unrelated `__name__`-reflection diagnostic helper, not
  a GraphQL-SDL-name table. `types/converters.py::SCALAR_MAP`'s
  `BigIntegerField -> BigInt` entries confirmed as the artifact describes: a
  distinct Django-field-to-scalar-type mapping, not a name string, correctly
  left alone. No missed consolidation found.
- **Concurrent dirty work not absorbed.** Diffed the baseline commit's copy of
  `inspect_django_type.py` directly (`git show
  daaa5ff4f885a339a4e5594fcf68d3c43cfb75d7:...`): the `graphql_type_name`
  bare-name matching and the SDL-named `_print_table` title Worker 1 flagged
  as "already dirty" were already present at the item baseline itself, i.e.
  pre-existing relative to this item and untouched by this edit - not
  absorbed into this consolidation, and the item-scoped diff confirms the
  edit's only touched lines are the import and the `_GRAPHQL_SCALAR_NAMES`
  entry.
- **Coverage gap check.** The one line `inspect_django_type.py` reports
  missing under the targeted run (`_resolve_bare_name`'s `continue` for an
  already-`seen` duplicate `type_cls`, part of the pre-existing bare-name
  dedup logic above) is unrelated to this item's scope and was present before
  this item's edit; an existing package-tier ambiguity test
  (`tests/management/test_inspect_django_type.py::test_ambiguous_bare_name_lists_copyable_dotted_paths`)
  covers the surrounding branch, and this specific `continue` is orthogonal to
  the `BigInt`-name consolidation. Not a defect introduced by this item.
- Formatting/lint re-verified independently: `uv run ruff format --check` and
  `uv run ruff check` clean on all three touched files;
  `scripts/check_trailing_commas.py --check` clean.

No revisions needed. Both edited call sites migrated, the rejected Upload
sites genuinely differ by design, and the flagged concurrent work was
confirmed pre-existing and untouched.

**Status: verified**

Plan item `scalars.py` checked in `docs/dry/dry-0_0_13.md`.
