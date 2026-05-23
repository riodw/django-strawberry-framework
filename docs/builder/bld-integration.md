# Build: Cross-slice integration pass

Spec reference: `docs/spec-019-multi_db-0_0_7.md`
Status: final-accepted

## Plan (Worker 1)

### DRY analysis across slices

The build touched three Python files with review-worthy logic and four
Markdown files. The integration scan walks each cross-cutting concern in
turn.

**Static-helper refresh.** Per BUILD.md "Cross-slice integration pass"
step 2, I refreshed shadow overviews for the three Python files touched
by the build:

- `docs/shadow/tests__types__test_resolvers.overview.md`
- `docs/shadow/tests__optimizer__test_multi_db.overview.md`
- `docs/shadow/examples__fakeshop__test_query__test_multi_db.overview.md`

Markdown targets (`docs/GLOSSARY.md`, `docs/README.md`, `KANBAN.md`,
`CHANGELOG.md`) get no helper run — the helper inspects Python.

#### Duplicated helpers across slices

Walked every helper / fixture introduced by Slices 1-3 against existing
sites:

- **Inlined `_sel(...)` and `_register_type_definition(...)`** at
  `tests/optimizer/test_multi_db.py:40-76` mirror
  `tests/optimizer/test_walker.py:46-103`. **Two users in the test tree**
  (walker + multi_db). The Slice 1 plan listed inline-vs-import as
  Worker 2 discretion, the inlined copy is intentionally narrower (drops
  the unused `field_map`/`primary` kwargs from the walker version), and
  no Slice 2 or Slice 3 site adds a third user. Worker 2's choice of
  inline preserved isolation between two unrelated test modules and
  avoided pulling test-module helpers across packages.
- **Slice 2's harness helpers** (`_seed_book_chain`, `_graphql_view`,
  `_build_test_schema`, `_MultiDbTestQuery`, `_current`, the temp
  `urlpatterns`) live entirely in
  `examples/fakeshop/test_query/test_multi_db.py`. Walked Slice 1 and
  Slice 3 for any reuse / mirror — none. The harness is scoped to one
  file by Decision 4 (no fakeshop schema modification) and Decision 7
  (do not pre-emptively factor); Slice 3 is docs-only and never touches
  test code.
- **Autouse `_reload_project_schema_for_acceptance_tests` fixture**
  copied verbatim from `examples/fakeshop/test_query/test_library_api.py:17-43`
  into `examples/fakeshop/test_query/test_multi_db.py:66-91`. Decision 7
  explicitly mandates the verbatim copy and forbids a `conftest.py`
  factoring until 3+ files need it. **Two users now** (`test_library_api`
  + `test_multi_db`); the spec's threshold is 3+. Worker 3's Slice 2
  review and Worker 1's Slice 2 final-verification both deferred the
  factoring decision to this integration pass. **Decision: do not
  consolidate.** Two users is below the threshold and the duplication is
  intentional per Decision 7; pre-emptively factoring would create a
  `conftest.py` whose entire content is a fixture that only two files
  use, which would be the wrong reuse abstraction for the current state.
  When a third `test_query/` file lands that needs the reload contract,
  that future card owns the factoring.

#### Inconsistent naming or error handling between slices

Walked every naming convention across the three new test files:

- **Test naming.** All seven new tests use snake_case verb-noun-detail
  shape and pin a single spec axis or branch each:
  - Slice 1 resolver-level: `test_fk_id_elision_stub_sets_state_db_via_router_db_for_read`,
    `..._router_call_passes_parent_row_as_instance`,
    `..._router_call_passes_none_instance_when_parent_lacks_state`,
    `..._returns_none_for_null_fk_and_does_not_call_router`,
    `test_strictness_check_is_connection_agnostic_under_non_default_alias`.
  - Slice 1 optimizer-plan: `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias`. Decision 3 axis 2 verified transitively by the Slice 2 live HTTP test per `AGENTS.md` line 9.
  - Slice 2 live HTTP: `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b`,
    `test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver`.

  Each name pins one axis or property. No collisions, no near-twins, no
  ambiguous abbreviations.

- **Docstring style.** Every new test has a one-line docstring naming
  the spec axis or branch (e.g. `"""Decision 3 axis 1 — stub's
  _state.db is set via router.db_for_read."""`). Convention-matching
  per spec rev2 S11; pyproject's `per-file-ignores` waives `D` / `ANN`
  on `tests/**/*.py` and `examples/**/*.py`.

- **Error-handling shape.** Slice 1 test (e) raises `OptimizerError`
  with the spec-pinned message `"Unplanned N+1: shelf"`. No Slice 2 or
  Slice 3 test asserts on `OptimizerError` (Slice 2 asserts on
  GraphQL JSON response shape; Slice 3 has no tests). One error class,
  one assertion site — no inconsistency.

- **Seeding-pattern naming.** Slice 1's resolver tests use
  `parent_row = Item(category_id=42)` (no DB write — un-saved Django
  model instance). Slice 1's optimizer-plan tests use
  `Item.objects.using("shard_b").all()` and
  `Category.objects.all()` (queryset shapes, no `.create(...)` calls).
  Slice 2's `_seed_book_chain(alias, *, title)` uses
  `.using(alias).create(...)` for the full
  `Branch → Shelf → Book` chain. Three distinct intent levels (un-saved
  instance fixture, queryset construction, live DB seed), each fitting
  its layer. No naming conflict.

#### Repeated ORM / queryset patterns

Walked every `Model.objects.using(alias)` call across the build:

- `tests/optimizer/test_multi_db.py:88` —
  `Item.objects.using("shard_b").all()`
- `tests/optimizer/test_multi_db.py:106` —
  `Item.objects.using("shard_b").all()` inside a `Prefetch`
- `examples/fakeshop/test_query/test_multi_db.py:136` —
  `models.Book.objects.using("shard_b").select_related(...)` inside
  the per-test `_MultiDbTestQuery` resolver
- `examples/fakeshop/test_query/test_multi_db.py:163-172` —
  `Branch.objects.using(alias).create(...)`,
  `Shelf.objects.using(alias).create(...)`,
  `Book.objects.using(alias).create(...)` inside `_seed_book_chain`

Four `.using("shard_b")` call sites in test code; one helper call site
that takes an `alias` parameter. The patterns are layer-appropriate:
unit tests use literal `"shard_b"` because the test pins the literal
alias; the live-HTTP seeder takes a parameter because it seeds on
multiple aliases. No centralization-into-helper opportunity surfaces —
the literal-vs-parameter split is correct.

#### Misplaced responsibilities between modules

Each slice's surface area matches the spec's per-slice file pin:

- Slice 1 lives entirely in `tests/` (package-internal). No leakage
  into `examples/`. Verified by `git diff` reading.
- Slice 2 lives entirely in `examples/fakeshop/test_query/`. Decision 4
  forbids modifying the fakeshop schemas, and Worker 2's diff is empty
  on `examples/fakeshop/apps/library/schema.py`,
  `examples/fakeshop/apps/products/schema.py`, and
  `examples/fakeshop/config/settings.py`. The temp URLConf and the
  per-test schema live inside the test file by Decision 6 rev3 R4 — the
  holder-pattern is intentionally local rather than a `conftest.py`.
- Slice 3 lives entirely in four `.md` files. No `.py` touched.
- Decision 7 explicitly forbids extracting Slice 2's harness or the
  autouse reload fixture into `conftest.py` until a second test file
  needs it — which Slice 2 itself is. The reasoning that *this* build
  does not factor is the spec's `do not pre-emptively factor` boundary:
  Slice 2 is the second user, but the spec's threshold is 3+ files.
  When the third file lands the factoring becomes a follow-up card.
- Zero production code change in `django_strawberry_framework/` across
  all three slices (Decision 2). Verified.

#### Missing or too-broad exports introduced by the build

- `git diff -- django_strawberry_framework/__init__.py` → empty.
  `__all__` and the re-export list are unchanged. Spec DoD item 16 and
  Slice 1/2/3 individual public-surface checks all confirm.
- No new symbol added by any slice. The build is tests + docs only.
- `pyproject.toml`, `django_strawberry_framework/__init__.py:__version__`,
  and `tests/base/test_init.py`'s version assertion are all unchanged
  per Decision 9 joint-cut policy (the last `0.0.7` card to ship owns
  the bump; this build is not that card).

#### Repeated string literals / dictionary keys / tuple shapes across slices

Walked the **Repeated string literals** sections of all three shadow
overviews and cross-referenced:

- **`tests/types/test_resolvers.overview.md`** repeats are dominated by
  pre-existing fakeshop conventions: `52x category`, `21x allItems`,
  `8x dst_optimizer_planned`, `7x category_id`,
  `7x dst_optimizer_strictness`, `5x allCategories`, `4x
  dst_optimizer_fk_id_elisions`. The five new Slice 1 tests reuse
  `category` / `category_id` (FK chain shape) and
  `dst_optimizer_planned` / `dst_optimizer_strictness` (strictness
  context dict keys) — all four are pre-existing convention in the file,
  not new repeats Slice 1 introduced.
- **`tests/optimizer/test_multi_db.overview.md`** reports
  `repeated string literals: 0`. The file's two tests use `shard_b` /
  `items` / `category` once each in load-bearing positions.
- **`examples/fakeshop/test_query/test_multi_db.overview.md`** reports
  8 repeats, all 2x: `apps.library.schema`, `config.schema`,
  the two-test verbatim GraphQL query body
  (`query { booksOnShardB { title shelf { code branch { name } } } }`),
  `/graphql/`, `application/json`, `booksOnShardB`, `default-only`,
  `shard-b-only`. The module-name pair (`apps.library.schema`,
  `config.schema`) is inside the verbatim-copied autouse reload fixture
  and matches `test_library_api.py:17-43`'s shape. The GraphQL string
  literal and the request-shape pair (`/graphql/`,
  `application/json`) are the two tests doing the same live HTTP shape
  with different seed data. `booksOnShardB` appears twice because both
  tests pull the same response field.

**Cross-file literal overlap.** Walked every literal in the union of
all three overviews:

| Literal | File 1 | File 2 | File 3 | Status |
|---|---|---|---|---|
| `shard_b` | resolvers (1x; not in Repeats) | optimizer (2x; not in Repeats) | fakeshop live (many; not in Repeats) | Load-bearing alias name; pinning it elsewhere would obscure the test's intent. Each test asserts on this exact string. |
| `default` | resolvers (mock return) | — | live (alias param) | Universal Django default — pinning behind a constant would hide a Django contract. |
| `category` / `category_id` | resolvers (52x / 7x) | optimizer (1x each) | — | Fakeshop FK chain shape; pre-existing convention in `tests/`. Slice 1 reuses it correctly. |
| `items` | — | optimizer (3x) | — | Relation name from the optimizer-plan test; one file, three uses (`_sel("items", ...)`, `Prefetch("items", ...)`, hint dict key `"items"`). Acceptable per the helper spec; consolidating into one constant inside the test would obscure the shape (the three uses are intentional shape pins, not accidental coupling). |
| `booksOnShardB` | — | — | live (2x) | GraphQL field name; both tests query the same field on the schema. Could be a module-level constant in the live HTTP file, but the cost is small (2x) and the spec rev5-post X7 widened test 2's query to match test 1's, so the duplication is a *consequence* of a spec-pinned shape, not an oversight. |
| `apps.library.schema` / `config.schema` | — | — | live (autouse fixture body) | Inside the verbatim-copied autouse reload fixture per Decision 7. Identical to `test_library_api.py:17-43` shape. |

**No cross-file repeated literals warrant consolidation.** The
intra-file repeats in the live HTTP file (the duplicated GraphQL query
body and the `override_settings(...) + clear_url_caches()` try/finally
block) were flagged by Worker 3 at Slice 2 review and deferred to this
pass. Walking them now: the query body is duplicated across the two
tests because spec rev5-post X7 widened test 2's body to match test 1's
shape; extracting it into a module-level `_BOOKS_QUERY` constant would
work mechanically but is at most a Low at the two-test scope and adds a
layer of indirection that does not yet pay for itself. The
`override_settings`/`clear_url_caches` block (10 lines, twice) is the
same: extracting a context manager helper would cut ~10 lines but adds a
new symbol and a layer of indirection for two callers. Both stay
inline; the cross-slice integration recommendation is to revisit if a
third live HTTP test enters the tree.

#### Whether comments now tell one coherent story

Walked the three new test files in slice order, reading each as a fresh
reader:

- `tests/optimizer/test_multi_db.py` opens with a module docstring
  explicitly cross-referencing the spec and the sibling resolver-test
  file. Inside the tests, comments cite spec lines for each axis pin
  (e.g. `# rev2 H2 — generated child querysets do NOT inherit the parent alias`).
- The five new tests in `tests/types/test_resolvers.py` carry one-line
  docstrings naming the axis pinned ("Decision 3 axis 1 — ..."), with
  inline comments citing the line ranges in
  `django_strawberry_framework/types/resolvers.py` that each branch
  exercises (e.g. `# types/resolvers.py:74-76 — early return None`).
- `examples/fakeshop/test_query/test_multi_db.py` opens with a 27-line
  module docstring explaining the live-HTTP harness, the holder
  pattern, the autouse reload fixture, the seeding contract, and the
  spec decisions that pin each piece. Each subsequent block carries
  matching inline comments.

A reader following the spec from Decision 3 axis 1 to axis 4 lands
correctly at the right test in the right file every time. Cross-file
breadcrumb is consistent.

### Cross-slice import / dependency review

Compared the **Imports** sections of the three shadow overviews against
the documented dependency boundary:

- `tests/types/test_resolvers.py`: imports from
  `apps.products.models` (fakeshop fixture models),
  `django_strawberry_framework` and submodules
  (`optimizer.field_meta`, `optimizer.plans`, `optimizer._context`,
  `types.resolvers`, `types.definition`, `exceptions`, `registry`),
  and standard-lib `types.SimpleNamespace` / `unittest.mock.Mock`. All
  consistent with the package-internal test scope.
- `tests/optimizer/test_multi_db.py`: imports from
  `apps.products.models`, `django.db.models.Prefetch`,
  `django_strawberry_framework` and submodules
  (`OptimizerHint`, `optimizer.field_meta`, `optimizer.walker`,
  `registry`, `types.definition`, `utils.strings`), and standard-lib
  `types.SimpleNamespace`. All first-party imports go through the
  package's public submodules (which are stable enough for tests); no
  reach-through into private members beyond what the spec authorizes
  (`_build_fk_id_stub`, `_check_n1` in the resolver-tests file are
  spec-named directly-tested private symbols).
- `examples/fakeshop/test_query/test_multi_db.py`: imports from
  `importlib`, `os`, `sys`, `pytest`, `strawberry`,
  `apps.library`, `django.test`, `django.urls`,
  `strawberry.django.views`, `strawberry.types`,
  `django_strawberry_framework` (only `DjangoOptimizerExtension` and
  `registry`), and an inside-fixture `apps.library.schema.BookType`
  import at line 130. The top-level `# noqa: E402` markers on the
  post-skip imports are load-bearing per Decision 6 and not the kind
  of suppression the slice checklist forbids.

**One-way dependency direction.** All imports flow upward — tests
import from `django_strawberry_framework`; package source imports
nothing from tests or fakeshop. Verified by the empty
`git diff -- django_strawberry_framework/`.

**Cross-test-tree imports.** None. No test file imports another test
file's symbols. Slice 1's `_sel` and `_register_type_definition` are
inlined rather than imported from `tests/optimizer/test_walker.py`
(Worker 2 chose the conservative posture); this preserves test-tree
isolation.

**Examples-to-package boundary.** The live HTTP test imports the
package's `DjangoOptimizerExtension` and `registry`, plus
`BookType` from the fakeshop `apps.library.schema` (inside the
fixture, after the registry reload). No package code reaches into
`examples/`; verified by `git diff -- django_strawberry_framework/`
being empty.

### Comments / documentation coherence

Walked the cross-doc wording landed by Slice 3 against the three test
files landed by Slices 1-2:

- **`docs/GLOSSARY.md` entry body** (`Multi-database cooperation` at
  lines 679-693) lists the four axes per spec Decision 3 in numbered
  list form. Bullet 1: `router.db_for_read` on FK-id elision stubs —
  matches Slice 1 tests (a)-(d) in `tests/types/test_resolvers.py`.
  Bullet 2: explicit `.using(alias)` `_db` preservation through
  `OptimizationPlan.apply` — matches Slice 1 test (f) in
  `tests/optimizer/test_multi_db.py`. Bullet 3: consumer-provided
  `Prefetch(queryset=...)` via `OptimizerHint.prefetch(...)` — matches
  Slice 1 test (g). Bullet 4: strictness-mode N+1 detection is
  connection-agnostic — matches Slice 1 test (e). All four bullets
  have a landed test pin.
- **`docs/README.md`** `### Sharded mode (multi-DB)` forward-pointer
  (line 218) enumerates the four narrowed axes in the same order as
  GLOSSARY, with link text pointing at the GLOSSARY anchor. Consistent.
- **`KANBAN.md`** `DONE-019-0.0.7` body cites all three test files by
  path and the four axes in the same order. The body lists test counts
  (5 resolver-level, 2 optimizer-plan, 2 live HTTP) that match the
  actual landed tests verbatim.
- **`CHANGELOG.md`** `[0.0.7]` `### Added` fourth bullet (line 33) is
  verbatim-pinned by spec line 576 and matches GLOSSARY / KANBAN /
  README in axis order and test-file references.

**Cross-doc wording consistency.** The four-axis enumeration is
identical in semantic content across all four documents (GLOSSARY /
README / KANBAN / CHANGELOG); only the formatting differs (numbered
list in GLOSSARY, prose with em-dashes in README/CHANGELOG/KANBAN).
The Worker 3 Slice 3 Low finding ("GLOSSARY bullets are stylistically
refined from spec line 563's flowing prose") was disposed as licensed
adaptation by Worker 1; the integration pass confirms that the
adaptation preserves all substantive content and is consistent with
the matching `for root querysets` suffix on bullet 2 in spec lines 569
(KANBAN body) and 576 (CHANGELOG bullet).

**Story coherence.** A reader starting at `docs/README.md`'s
`### Sharded mode (multi-DB)` section follows the forward-pointer to
`docs/GLOSSARY.md#multi-database-cooperation`, sees the four axes,
follows the cross-references to `DjangoOptimizerExtension`,
`get_queryset visibility hook`, `OptimizerHint`, `FK-id elision`, and
`Strictness mode`. Each cross-reference resolves to a live anchor.
The KANBAN Done body and CHANGELOG bullet both link to
`docs/spec-019-multi_db-0_0_7.md` (active path) and the three test
files. No broken anchors; no contradictory wording.

### Consolidation recommendations

**None.** The integration scan found three intentional duplication
sites that the spec already authorizes and one observation that does
not warrant consolidation at the current scope:

1. **Inlined `_sel` / `_register_type_definition` in
   `tests/optimizer/test_multi_db.py`** — two users (walker + multi_db).
   Slice 1 plan listed inline-vs-import as Worker 2 discretion;
   inlined copy is intentionally narrower; no third user appears in
   this build. Below the threshold a shared `tests/optimizer/_helpers.py`
   would justify.
2. **Autouse `_reload_project_schema_for_acceptance_tests` fixture
   verbatim from `test_library_api.py:17-43`** — two users now
   (`test_library_api` + `test_multi_db`). Decision 7 explicitly
   forbids `conftest.py` extraction until 3+ files need it; this build
   is the second user.
3. **Within-file duplicates in
   `examples/fakeshop/test_query/test_multi_db.py`** — duplicated
   GraphQL query body (rev5-post X7 spec consequence) and duplicated
   `override_settings + clear_url_caches` try/finally block. Two
   callers each, ~10 lines each. Extracting either into a module-level
   constant or a context manager would add a layer of indirection for
   two-caller surfaces; the spec-pinned shapes read more clearly
   inline at the current scope.

The cross-doc wording (GLOSSARY / CHANGELOG / KANBAN / README) is
intentionally redundant per Slice 3 plan line 10: each surface needs
its own version of the contract for its readership; the spec pins
each block separately at lines 563 / 566 / 569 / 576 and Worker 3's
Slice 3 documentation/release sanity check confirmed the verbatim
matches (the one Low finding on the GLOSSARY bullet adaptation was
disposed as licensed by Worker 1).

Carry-forward to the next spec author / next multi_db follow-up card:
when a **third** consumer of any of the three intentional duplications
above lands, that future card owns the factoring decision:
`tests/optimizer/_helpers.py` for the walker-test fixtures, an
`examples/fakeshop/test_query/conftest.py` for the autouse reload
fixture, or a module-local context-manager extraction for the live
HTTP harness. The integration pass records these as deferred-by-design
rather than oversights.

## Final verification (Worker 1)

### Summary

Cross-slice integration scan walked the three new Python files
(`tests/types/test_resolvers.py` extension; new
`tests/optimizer/test_multi_db.py`; new
`examples/fakeshop/test_query/test_multi_db.py`) and four Slice 3
Markdown targets (`docs/GLOSSARY.md`, `docs/README.md`, `KANBAN.md`,
`CHANGELOG.md`) for cross-cutting concerns: duplicated helpers,
inconsistent naming or error handling, repeated ORM/queryset patterns,
misplaced responsibilities, public-export drift, cross-file repeated
literals, and cross-doc story coherence. Refreshed the three shadow
overviews under `docs/shadow/` and compared their Repeated string
literals and Imports sections; walked every prior slice artifact's
`What looks solid` / `DRY findings` / `Notes for Worker 1` sections.

Found three intentional duplication sites (inlined `_sel` /
`_register_type_definition` from `test_walker.py` into
`test_multi_db.py`; autouse reload fixture copied verbatim from
`test_library_api.py` into the live multi-db file per Decision 7;
within-file GraphQL query and `override_settings` block duplication in
the live-HTTP test file). Each is below the spec's threshold for
consolidation (3+ users, second test file in the tree, or two-caller
shapes that don't pay for an extracted abstraction). The cross-doc
wording (GLOSSARY / CHANGELOG / KANBAN / README) is consistent — the
four-axis enumeration matches semantically across all four documents,
and the verbatim-pinned blocks at spec lines 566 / 569 / 576 landed
character-for-character per Worker 3's Slice 3 diff checks.

`git diff -- django_strawberry_framework/__init__.py` is empty (no
public-export drift); `git diff -- django_strawberry_framework/` is
empty (no production code change, per Decision 2). Setting integration
status to `final-accepted` directly — no consolidation loop required.

### Spec changes made (Worker 1 only)

None.
