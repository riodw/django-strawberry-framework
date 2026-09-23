# Build: Close cycle — Cohort A, the evaluation-state carry at the raw-list seam — superseded historical record

Spec reference: `docs/spec-050-list_field_arguments-0_0_15.md`, re-pinned at final verification
after the spec edits recorded in `### Spec changes made (Worker 1 only)` (Decision 8;
`## Slice checklist` Slice 3; Decision 5 step 4; `## Test plan` -> `### Package tier` seal-axis
bullet; `## Test plan` -> `### The raw-list row source`; `## Definition of done` — cited by
heading; the line pins first recorded here matched no committed spec revision)
Status: superseded cohort artifact (final-accepted only for its pre-candidate snapshot)

Superseded, not evidence. The measurements below describe the pre-candidate snapshot
`20646db2` plus working-tree paths. The gated candidate is `2c66416e` (tree `5ce4c799`) and the
evidence-only follow-up is `b38184b3`; the gate and the Decision 20 review of that exact tree are in
`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Closing record`. Working-tree
measurements (digests, md5s, sweep counts) are not reproducible from any commit.

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** The package-wide AST inventory was refreshed this pass
(`<scratch>/inspect/helper-inventory.md`, 2,254 lines over every `django_strawberry_framework/**.py`)
and `scripts/review_inspect.py` was run on `django_strawberry_framework/utils/querysets.py`
(`<scratch>/inspect/django_strawberry_framework__utils__querysets.overview.md`). Shapes searched:
`cache`, `result_cache`, `evaluat`, `materializ`, `seal`, `normaliz`, `window`, `rows(`. Relevant
candidates found, all in `django_strawberry_framework/utils/querysets.py`:
`_seal_or_defect`, `_SealPolicy`, `_readable_queryset_state`, `materialized_rows`,
`normalized_row_source`, `_row_source_model`, `_raw_list_source_message`. No helper that carries,
copies, or validates fetched rows exists anywhere else in the package — `materialized_rows` is the
only reader of `_result_cache` at this seam, and
`django_strawberry_framework/optimizer/extension.py` reads it only as an already-evaluated signal
on a different surface. **No new helper is justified**; the carry is an axis on the existing
policy object.

- **Existing patterns reused.**
  - `django_strawberry_framework/utils/querysets.py::_SealPolicy` — the declared-once per-surface
    option set. Every surface differs from the default on one or two axes and the axis lives here
    rather than as a keyword threaded through five signatures. The carry is the next axis.
  - `django_strawberry_framework/utils/querysets.py::_seal_or_defect` — already reads the
    candidate's instance state once through `_readable_queryset_state`
    (`object.__getattribute__`), validates every slot it copies forward, and reproduces exactly
    what `QuerySet._clone` copies (`_iterable_class`, `_fields`, `_prefetch_related_lookups`,
    `_sticky_filter`, `_for_write`). The carry is one more slot from the SAME state dict, so
    validation and execution still provably cannot diverge.
  - `django_strawberry_framework/utils/querysets.py::materialized_rows` — the existing
    exact-type-only read of `_result_cache`. It needs no code change: once
    `normalized_row_source` returns an exact queryset that carries the rows,
    `django_strawberry_framework/types/resolvers.py` many-side resolver reads them through it
    unchanged.
  - The `("untrusted", ...)` defect code and its existing arm in
    `django_strawberry_framework/utils/querysets.py::_raw_list_source_message`. The overview
    counts 72 occurrences of the `untrusted` literal in this module with no named constant, so a
    new site reuses the established spelling and introduces no constant.
  - Live probe idiom: `examples/fakeshop/test_query/test_resource_policy_api.py`
    `#"def _hostile_relation_manager"` (a context manager that changes real Django relation-manager
    wiring and restores it in `finally`), `#"def _hostile_relation_schema"` (a `@cache`d probe
    schema keyed on the reloaded type), and its two mounted views. The new rows copy that shape
    rather than inventing a second one.
  - Package idiom: `tests/test_resource_policy.py`
    `#"def test_an_exact_queryset_still_carries_the_row_bound_into_sql"` (seed, `SimpleNamespace`
    info, `stash_resource_policy`) and `tests/utils/test_querysets.py::test_seal_require_unevaluated`
    (a policy built explicitly, then `_seal_or_defect` called directly).

- **New helpers justified.** None. One new **field** on `_SealPolicy`
  (`carry_result_cache: bool = False`), set on `_RAW_LIST_SOURCE_POLICY` only, plus its validation
  and its copy inside `_seal_or_defect`. Single responsibility: whether this surface's rebuild
  carries the source's fetched rows forward.

- **Duplication risk avoided.** The naive implementation copies the cache inside
  `normalized_row_source` after the seal returns. That splits "what a faithful rebuild carries
  forward" across two functions — `_seal_or_defect` would own five slots and
  `normalized_row_source` a sixth — and it re-reads the instance state a second time, so the
  validated state and the executed state could drift, which is exactly the property
  `_seal_or_defect`'s docstring claims. It also puts a bare `sealed._result_cache = ...` write
  outside the only function allowed to know what a sealed queryset's internals are. **Rejected:
  the axis goes on the policy and the copy happens in the sealer**, next to the other five.

  The second risk is a second validation of the same shape: the carried cache needs a type check
  (below), and `_queryset_state_defect` already owns "is this state slot shaped the way Django
  makes it". The check is written once, in `_seal_or_defect`, gated on the policy axis, emitting
  the existing `untrusted` code — never a second code, a second message arm, or a second helper.

### Shared shapes across the two concurrent cohorts

The partition is `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`
`## Close cycle (Decision 22)`; Cohort B owns `docs/README.md` and `README.md` and nothing else
(the DONE record's partition now also folds `schema.py` into Cohort B).
Three shapes both cohorts could touch, each assigned to exactly one owner:

1. **The documented schema spelling in an executable example.** Owner: **Cohort B**
   (`docs/README.md`). Cohort A **cites it as reuse**: the new live probe schema is built with
   `DjangoSchema(...)` and installs the optimizer as a class entry or a factory — never a plain
   `strawberry.Schema` and never a bare extension instance — so the two cohorts cannot publish
   contradictory spellings of the same recipe.
2. **The trust-contract prose of Decision 20.** Owner: **Cohort B**. Cohort A states behavior
   only: no docstring, comment, or test name in Cohort A restates the trust levels or the
   admission rule. A test docstring says what the row pins, not what the package trusts.
3. **The evaluation-carry wording** ("a source that arrives evaluated is windowed from the rows
   it holds"). Owner: **Cohort A** (docstrings in `utils/querysets.py`, `resource_policy.py`,
   `types/resolvers.py`). Cohort B does not state it: `docs/README.md`'s list-field section
   documents arguments and bounds, not evaluation state, and no Cohort B row asks for it.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before
editing — another worker's pass may have shifted the file since this plan was written.

**Before the first edit to any owned file:** `git diff HEAD -- <path>` must print nothing (a
concurrent DRY cycle names `django_strawberry_framework/utils/querysets.py`). All eleven owned
paths (the committed partition had nine code paths before the fold-in) were clean at plan time. If one is not, stop and report it here rather than editing.

1. `django_strawberry_framework/utils/querysets.py::_SealPolicy` (~line 2719) — add
   `carry_result_cache: bool = False` as the last field, and one docstring bullet for it in the
   axis list. The bullet states: the rebuild carries the source's fetched rows forward, read from
   the same instance state every other slot comes from, so a source that already holds rows is
   windowed from them instead of being re-queried; it is on for the raw-list row source alone,
   the one surface where nothing is composed after the rebuild; it is the complement of
   `require_unevaluated` and no policy sets both.
2. Same file, the `require_unevaluated` bullet (~line 2754) — leave its rule intact. Its closing
   sentence ("A consumer that evaluates inside the hook pays for the discarded `_result_cache` in
   one extra query, which is a cost, not a broken seal") stays true for every `get_queryset` seal
   and must not be rewritten into a claim about the raw-list seam.
3. Same file, `_RAW_LIST_SOURCE_POLICY` (~line 2810) — set `carry_result_cache=True` and rewrite
   the comment clause "a source the consumer already evaluated is a cost (one discarded result
   cache, one more query) rather than a broken seal" to state the carry: the rows travel with the
   source, so a project queryset class costs what Django's own manager costs. Keep the rest of
   that comment (nothing recomposes here; the rebuild itself is not optional).
4. Same file, `_seal_or_defect` (~line 3289, immediately BEFORE the `policy.require_unevaluated`
   check so the reused `untrusted` code keeps its fixed position ahead of `evaluated` in the
   canonical ordering) — read `state.get("_result_cache")` once into a local, and when
   `policy.carry_result_cache` and the value is not `None` and `type(value) is not list`, return
   `None, ("untrusted", f"{cls_name}._result_cache is a {_safe_type_name(value)}")`.
   **`type(...) is list`, never `isinstance`:** a `list` subclass brings its own `__getitem__`, and
   `QuerySet.__getitem__` returns `self._result_cache[k]` when the cache is populated — carrying a
   subclass would put the raw-list ceiling back inside consumer code, which is the one thing this
   seam exists to prevent. Django only ever stores an exact `list` here, so the refusal is
   fail-closed on state Django does not produce.
5. Same file, the state-copy block at the end of `_seal_or_defect` (~line 3323, beside
   `sealed._iterable_class = ...`) — assign the carried rows when `policy.carry_result_cache`,
   and leave `_result_cache` at the `None` `models.QuerySet.__init__` already set otherwise. The
   list object is taken as-is, **not copied**: `materialized_rows` already hands Django's own list
   out uncopied on the exact-queryset path, the row objects are shared either way, and an O(n)
   copy per rebuilt subclass would be a per-parent-row cost on the relation branch this change
   exists to make cheaper. Keep the `_known_related_objects` drop and its comment unchanged.
6. Same file, `_seal_or_defect`'s docstring `untrusted` defect paragraph — add the `_result_cache`
   shape clause to the enumeration of what cannot be faithfully rebuilt. No new code, so no new
   arm at any message site.
7. Same file, `normalized_row_source` (~line 3357) — replace the final paragraph ("The rebuilt
   queryset is unevaluated even when the candidate had rows cached, so a subclass source costs one
   extra query. That is the price of the bound being enforceable at all…") with the carry: the
   rebuild brings the source's fetched rows with it, so a subclass that arrives evaluated is
   windowed from the rows it holds and costs no query the exact shape would not have cost; what
   the rebuild drops is the subclass's own methods. Keep the three-bullet shape list and the
   `type(value)`-not-`isinstance` reasoning intact.
8. Same file, `materialized_rows` (~line 3402) — extend the docstring so the exact-type rule reads
   as the reason it is correct rather than as a claim that a subclass has no rows to give: a
   subclass answers `None` here because its `__dict__` is not Django's own slot on a
   package-owned object; the rows of a subclass source reach a caller through
   `normalized_row_source`'s rebuild instead. Do not weaken the exact-type rule.
9. Same file, `_prepared_visibility_source` docstring (~line 3673) — the clause "an
   already-evaluated source seals to a fresh, unevaluated queryset (the seal never copies
   `_result_cache`), so cached rows never reach the hook" is now false as an unqualified statement
   about the seal. Scope it to this seal / this policy: the visibility seal does not carry the
   cache, so cached rows never reach the hook. One sentence, same place.
10. `django_strawberry_framework/resource_policy.py::_windowed_rows` — add one sentence to the
    docstring: a source that arrives evaluated is windowed from the rows it already holds, because
    `QuerySet.__getitem__` reads a populated `_result_cache` directly, so the window costs no
    query for the exact shape and for a rebuilt subclass alike. No code change in this module.
11. `django_strawberry_framework/types/resolvers.py` many-side resolver, the comment block ending
    `#"or the subclass is rebuilt and answers no cached rows at all, which is one extra query"` (the
    quoted text spans two source lines) —
    correct it: the cache entry is normalized first so the rows come out of Django's own slot on
    an object this package owns, and a rebuilt subclass carries those same rows, so the prefetched
    path costs no query whichever class the relation manager builds. **No code change in this
    module** — `normalized_row_source` -> `materialized_rows` -> `bounded_rows` already reads the
    carried rows once the seal carries them.

### Test additions / updates

No `--cov*` flag in any command. Focused runs only; the full sweep belongs to the final gate.

**Package tier — `tests/test_resource_policy.py`** (beside the existing raw-list-source rows,
`#"class _EscapingQuerySet"` through `#"def test_an_exact_queryset_still_carries_the_row_bound_into_sql"`):

- A module-level `QuerySet` subclass with **no overrides** standing for a project queryset class
  (the spec's shape: what `QuerySet.as_manager()` / `Manager.from_queryset` gives a model). It is a
  distinct class from `_EscapingQuerySet`, whose whole point is a hostile `__getitem__`.
- P1 — an **evaluated exact queryset** through `bounded_rows`: zero queries during the call, rows
  equal to the leading window of what the source held.
- P2 — an **evaluated project subclass** through `bounded_rows`: zero queries, rows equal to the
  leading window, and the returned object is an exact `QuerySet` (the rebuild happened).
- P3 — the same subclass through `bounded_rows_async`: zero queries, the same rows under the async
  adapter rather than a second fetch.
- P4 — the evaluated exact queryset through `bounded_rows_async`: zero queries.
- P5 — `_windowed_rows` over the evaluated subclass with `offset=1, requested_limit=2`: the two
  expected rows, zero queries (the coordinate window is taken over the carried rows).
- B2 / B3 — a subclass whose `_result_cache` is a **lying sequence** (an object whose
  `__getitem__` returns every row) through `bounded_rows` and through `bounded_rows_async`: a typed
  `ConfigurationError`, and the liar's rows never reach the caller.
- The docstring of `tests/test_resource_policy.py::test_a_queryset_subclass_is_never_asked_what_it_has_already_fetched`
  is reworded so it states the live rule — `materialized_rows` reads Django's own slot on an exact
  queryset, so a subclass answers nothing there — without implying that a subclass source has no
  rows to give. The assertion itself (`materialized_rows(hostile) is None`) stays exactly as it is.

**Query counting, package tier:** use the instrument already used in `tests/`
(`django_assert_num_queries` or `CaptureQueriesContext(connection)`); assert an **absolute zero**,
never only an equality. For the async rows, `pytest.mark.django_db(transaction=True)` plus the
`sync_to_async(seed_data)` seeding idiom the neighbouring async rows use.

**Sealer admission — `tests/utils/test_querysets.py`** (beside `test_seal_require_unevaluated`):

- B1 — `_seal_or_defect` under a policy with `carry_result_cache=True`: an exact-`list`
  `_result_cache` is carried onto the sealed queryset (`sealed._result_cache` is the same list),
  while a non-exact-`list` populated cache returns
  `("untrusted", "<class>._result_cache is a <type>")` and no sealed queryset. A `list` SUBCLASS is
  one of the parametrized cases, because that is the shape whose `__getitem__` would answer the
  ceiling.
- `test_seal_require_unevaluated` is unchanged: it constructs `_SealPolicy` by keyword, so a new
  defaulted field does not touch it, and the OrderSet seal's `evaluated` verdict still stands.

**Live tier — `examples/fakeshop/test_query/test_resource_policy_api.py`**:

- A `Manager.from_queryset` mount, in the idiom of `#"def _hostile_relation_manager"`: build
  `models.Manager.from_queryset(<a QuerySet subclass with no overrides>)` at module level and, for
  the duration of the row, make the reverse `Patron.loans` manager build its querysets from that
  manager's queryset class, restoring in `finally`. Deriving the mounted class **from** a real
  `Manager.from_queryset` result is what makes the row about that documented Django shape rather
  than about an ad-hoc subclass.
- A probe schema with the **optimizer installed** (`DjangoSchema(..., extensions=[...])`, class or
  factory entry — see shared shape 1) over the same `patrons { loans }` root
  `#"def _hostile_relation_schema"` declares, with its own `max_list_rows`. The existing hostile
  schema installs no optimizer, so it plans no prefetch and cannot exercise the prefetched branch
  the carry lives on. Two mounts, sync and async, beside `rp-hostile-relation/`.
- L1 — **the load-bearing row**, parametrized over **two parent cardinalities** (e.g. 2 and 3
  patrons, each with several loans): the same document, over the same mount, run once with the
  `Manager.from_queryset` mount active and once with Django's own manager, asserting (a) the two
  query counts are **equal** and (b) the count is the **absolute** number a prefetching plan costs
  — derived from a real run, never guessed. An equality alone is vacuous; the absolute number is
  what proves the plan prefetched rather than that both paths were equally slow, and the second
  cardinality is what distinguishes a prefetch from an N+1.
- L2 — the async transport: the same document over the `AsyncDjangoGraphQLView` mount returns the
  same rows. **Instrument warning:** `CaptureQueriesContext` is bound to the calling thread's
  connection, and async live rows run their ORM work through `sync_to_async` worker threads, so an
  empty capture reads exactly like a green zero. Assert an absolute, non-zero control count in the
  same row if a count is asserted at all; if the capture cannot be made honest, assert rows only
  and record that in the build report rather than shipping a count nobody can trust.
- The module docstring's "Row groups" enumeration (`#"the collection bounds the fields enforce"`)
  gains the prefetched-relation cost where it belongs — the docstring is the authoritative
  description of the suite.

**No change is planned in `examples/fakeshop/apps/library/models.py`,
`examples/fakeshop/test_query/test_library_api.py`, or
`examples/fakeshop/test_query/test_relations_async_api.py`.** (superseded by P2-2: `Loan` declares `objects = LoanQuerySet.as_manager()`) They stay in the cohort's ownership
so a surprise re-pin has an owner, but the plan needs none: see the model decision below.

**Temp tests for Worker 3:** a scratch row under `docs/builder/temp-tests/050/close-row_carry/`
that calls `bounded_rows` on an evaluated subclass while counting queries is the cheapest way to
check that P2 is distinguishing (it fails on a tree without the carry). Delete or promote per the
artifact contract.

### Why the `Manager.from_queryset` shape is mounted at the probe, not declared on a model

Superseded by P2-2: `Loan` declares `objects = LoanQuerySet.as_manager()`; the mount argument
below is historical.

The spec's live row needs a relation that (a) is a many-side raw list, (b) whose **target type
declares no custom `get_queryset`** — the one branch with no visibility rebuild in front of it, and
the only branch that reaches `normalized_row_source` on the prefetch cache — and (c) is planned as
a prefetch.

- In the library app, `LoanType` is taken as the only many-side target that declares no
  `get_queryset` (wrong: `GenreType`, via the `Book.genres` M2M, declares none either)
  (`ShelfType`, `BookType`, `IssueType` and the connection-shaped `Periodical.issues` all do), so
  the relation is `Patron.loans` or `Book.loans` either way.
- **A model-level declaration removes the control.** `Loan.objects = Manager.from_queryset(...)()`
  makes *every* loans relation a subclass source, so no plain-manager relation of the same shape
  survives to be the control, and the load-bearing assertion is precisely an equality with the
  plain manager **on the same request shape**. The control would have to move to a different model
  and a different relation, which is a different shape and a weaker claim.
- **The mount keeps the control exact** — same relation, same document, same seed, manager mounted
  or not — and costs no re-pin anywhere else in the tree, where a model-level change would push
  subclass querysets through every loans path in the library and async relation suites for no
  additional evidence.
- It is still the documented Django shape, not a test double: the mounted queryset class comes from
  a genuine `models.Manager.from_queryset(...)` result, Django's own related-manager machinery
  builds the relation manager and the prefetch cache from it, and no framework seam is bypassed —
  the same argument `#"def _hostile_relation_manager"` already makes for its own mount.
- `examples/fakeshop/apps/library/models.py` therefore stays unedited (superseded by P2-2: `Loan` declares `objects = LoanQuerySet.as_manager()`) and no migration question
  arises. The final gate runs `manage.py makemigrations --check --dry-run` anyway; if a builder
  ever does change a model here, that command is the check, and a manager-only change generates no
  migration.

### Boundary count and the split question

**One** new boundary: the `untrusted` refusal of a `_result_cache` that is not an exact `list`
(step 4). The carry itself is not a refusal boundary, but not only a cost — it says no to
nothing, yet without it the async relation path breaks (measured at `ae52bdec`: without the carry, L2 fails with `data` None because graphql-core
iterates the lazily sliced rebuild on the event loop and Django raises `SynchronousOnlyOperation`,
and both L1 cardinalities fail with `assert 4 == 2`). One boundary is one mutate / run / count / revert / byte-compare loop, so **the cohort is
not split**; the docstring corrections and the tests travel with the single behavior change they
describe and would review worse apart.

### Failability

- **The new boundary (step 4)** owes a full proof: mutation = delete the `type(...) is list` check
  so a populated non-list cache is carried. Expected failing rows: B1 (sealer admission), B2 and B3
  (the lying sequence through both colors) — three rows, above the weakly-pinned threshold.
- **The carry is not a refusal boundary, but not only a cost, and owes no boundary proof**, but the plan requires its rows to be
  distinguishing: a mutation that sets `carry_result_cache=False` on `_RAW_LIST_SOURCE_POLICY` must
  fail **at least two rows per tier** — P2 and P3 in the package tier, and both parametrized cases
  of L1 in the live tier. Record that measurement in `### Failability proofs` beside the boundary
  entry even though it refuses nothing; a carry that only one row can see is weakly pinned in
  the sense that matters here. Discharged at `ae52bdec`: under the mutation L1 fails at both
  cardinalities (`assert 4 == 2`) and L2 fails (`data` None).

### Hot-path budget

Declared hot-path by the plan
(`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Close cycle (Decision 22)`). The
number owed: **the query count for one prefetched `Manager.from_queryset` relation request, before
and after, beside Django's own manager on the same document and the same seed.** Drive it with the
L1 document at the larger parent cardinality, measured with the same capture instrument both times;
report before, after, delta, and the plain-manager control's count in all three columns. A count is
a reproducible metric, so no iteration statistic is needed; the exact command belongs in the build
report.

### Floor verification

Owned by **this build pass** for the two package modules; the full twenty-three-path scope (the floor at `f7192bfb`; 27 at HEAD) is the
final gate's (`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`
`### Floor-verification scope`). The versions and recipe are copied from
`docs/builder/BUILD.md` `## Floor verification`, which is their single canonical statement: Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**.

```shell
uv venv <scratch>/dsf-floor --python 3.10
uv pip install --python <scratch>/dsf-floor/bin/python -e . --group dev
uv pip install --python <scratch>/dsf-floor/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'
<scratch>/dsf-floor/bin/python -m pytest tests/test_resource_policy.py tests/utils/test_querysets.py --no-cov
```

Never install into the shared `.venv`; the explicit `--python` is what keeps it out. Record the
venv path, the resolved versions as read by `uv pip list --python <scratch>/dsf-floor/bin/python`,
the scope as run, and pass/fail.

### Implementation discretion items

Assessed and decided to be Worker 2's:

- The name of the no-override `QuerySet` subclass and of the mounted manager in each test module,
  and whether the live mount is a `@contextmanager` or a fixture.
- The exact parent cardinalities and seed sizes for L1, provided there are at least two
  cardinalities and more loans per patron than one.
- Whether the local in `_seal_or_defect` holding the cache is read before or after the prefetch
  seal, so long as the `untrusted` return precedes the `evaluated` check.
- `django_assert_num_queries` versus `CaptureQueriesContext` per row, and the `@cache` key shape of
  the new probe schema (it must follow the type-as-argument rule the neighbouring factory
  documents).
- The wording of every docstring listed above, within the contract each step states.

### Spec slice checklist (verbatim)

Re-quoted at final verification from the spec as it stands after every `### Spec changes made
(Worker 1 only)` edit below, so the text a tick is audited against is the text the spec demands.
Measured before P2-2: this text occurs 0 times in the committed spec (`f7192bfb` and HEAD).
`## Slice checklist` Slice 3's raw-list row, then the `## Definition of done` row Decision 8
owns:

- [x] The raw-list seam windows a source that arrives evaluated from the rows it already
      holds, exact queryset and rebuilt subclass alike, with the query count pinned at zero
      in the package tier and a `Manager.from_queryset` relation pinned live at Django's own
      manager's absolute count, its pending reverse-relation predicate baked onto the
      rebuild by the same unbound `Query.add_q` an exact queryset's is, and a deferred-filter
      state Django never writes refused with the typed error at both tiers.
- [x] A source that arrives evaluated is windowed from the rows it holds with no further
      query, exact queryset and rebuilt subclass alike, through `bounded_rows` and
      `bounded_rows_async`; a relation whose manager is a `Manager.from_queryset` class with
      no overrides returns the same rows at the same ABSOLUTE query count as Django's own
      manager, proven live under a prefetching plan at two parent cardinalities, and returns
      those same rows on the async transport, where a query capture opened on the calling
      thread cannot see the work a `sync_to_async` worker thread does (Decision 8).

Tick warrant, clause by clause against the diff (Worker 1, final verification). Package-tier
window from held rows, exact and rebuilt subclass alike, both colors: P1-P5. Count pinned at an
absolute zero in the package tier: `django_assert_num_queries(0)` on the three sync rows, the two
async rows asserting row identity because a capture on the calling thread cannot see a
`sync_to_async` worker's ORM work. The `Manager.from_queryset` relation at Django's own manager's
absolute count, live, under a prefetching plan, at two parent cardinalities:
`test_a_project_queryset_class_relation_costs_what_djangos_own_manager_costs[two-parents]` and
`[three-parents]` (renamed by P2-2 to `…costs_two_prefetch_queries`, one arm), asserting the identical payload and
`CARRY_RELATION_QUERIES = 2` on both arms.
The same rows on the async transport:
`test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited`. The pending
reverse-relation predicate baked by the same unbound `Query.add_q`: P6 and
`test_a_subclass_result_with_a_pending_deferred_filter_seals_with_it_baked`: P6 through Django's
own `_apply_rel_filters`; the flipped seal row hand-plants `(False, (), {"name": "later"})`. A deferred-filter state Django never writes
refused with the typed error at both tiers: R1's four cases, R2, R3, and the two live
`[malformed-deferred-filter]` rows. Every clause has a row, and the failability re-run below
shows each of those rows failing when the behavior it names is removed - so none is green by
accident. Both boxes are ticked; nothing is deferred.

### Notes for Worker 1 (spec reconciliation)

- **`docs/GLOSSARY.md` "Sealed execution queryset" is falsified by this cohort.** Its body states
  that "`_result_cache` / `_known_related_objects` are never copied forward" for
  `django_strawberry_framework/utils/querysets.py::_seal_or_defect`. After the carry that is true
  of every policy except `_RAW_LIST_SOURCE_POLICY`. The glossary is DB-backed and is in **no
  cohort's writable set** this cycle, and the spec's `## Doc updates` glossary bullet names only
  `DjangoListField`, `OrderSet` and the execution resource policy bodies — so no owner currently
  carries this correction. It belongs with the close cycle's board/glossary regenerate step. Route
  it to the maintainer. (`docs/GLOSSARY.md`, `docs/TREE.md`, `examples/fakeshop/test_query/README.md`,
  `examples/fakeshop/test_query/test_debug_toolbar_api.py` and `tests/middleware/` were also dirty
  from a concurrent session at plan time, beyond the plan's recorded baseline-dirty list; none is
  owned by either cohort and none is touched.)

  **The exact replacement sentence, so the DB pass is a paste and not a rewrite.** In the
  `GlossaryTerm` body for `Sealed execution queryset`, replace

  > The consumer's subclass identity — its executable override dispatch, the leak vector — is
  > deliberately dropped, and `_result_cache` / `_known_related_objects` are never copied
  > forward, so no cached or synthetic row and no shadowed `.all()` / `.filter()` / `.first()` /
  > `.__aiter__()` / `Query.chain` can cross the boundary.

  with

  > The consumer's subclass identity — its executable override dispatch, the leak vector — is
  > deliberately dropped, and `_known_related_objects` is never copied forward, so no synthetic
  > row and no shadowed `.all()` / `.filter()` / `.first()` / `.__aiter__()` / `Query.chain` can
  > cross the boundary. `_result_cache` is carried forward by the raw-list row source's policy
  > alone, where nothing is composed after the rebuild and a source that arrives evaluated is
  > windowed from the rows it already holds; every other policy leaves it `None`, and a
  > populated cache that is not an exact `list` is refused rather than carried.

  Edit the DB via the ORM and regenerate `docs/GLOSSARY.md`; a hand edit to the rendered file is
  reverted by the next render and goes red in CI's generator `--check`.

- **Two archived specs enumerate the pending-`_deferred_filter` refusal and are made imprecise by
  the admission change** (`docs/SPECS/spec-045-visibility_boundary-0_0_14.md`
  #"unresolved deferred filter, unsealable prefetch child" and
  `docs/SPECS/spec-034-permissions-0_0_10.md` #"an unresolved deferred filter"). Both list it as
  an example of state that cannot be sealed; after this change only a MALFORMED deferred filter
  is. Neither is in any cohort's writable set, and amending a shipped spec is a round over that
  spec (`docs/builder/BUILD.md` `### Cohorting, naming, and closure`), not a slice edit. Routed
  to the maintainer with the one-word fix: "unresolved" becomes "malformed" in both sentences.
- The spec's `## Test plan` -> `### The raw-list row source` says the package-tier evaluated
  subclass is "a `QuerySet.as_manager()` class with no overrides" while the Slice 3 row and the
  Definition of done both say `Manager.from_queryset`. They are the same Django shape (a project
  queryset class behind a model's default manager) and the plan treats them as one; no spec edit
  is needed, but a reader comparing the two homes should not read them as two requirements.

### Spec changes made (Worker 1 only)

- `docs/spec-050-list_field_arguments-0_0_15-rationale.md` `### Decision 8 …`, the final rejected
  alternative ("Reading the relation cache's `_result_cache` with `getattr` after normalizing"):
  its closing clause "a subclass answers no cached rows and costs one query" is falsified by
  Decision 8 as the spec now states it, and Worker 3 reads this file against the implementation
  during review. The rejection itself stands and is kept; the falsified consequence is deleted and
  replaced by what the rebuild now does. Rationale rule 2 (`docs/builder/worker-1.md`
  `### Performing the rationale move`): falsified prose is deleted, not moved.
- No edit to `docs/spec-050-list_field_arguments-0_0_15.md`. Its header, `Status:` and revision
  lines already describe the carry as the current contract.

**Plan-revision pass.** Triggered by the structural-drift pause. The fixed contract (the sealer
admits a pending reverse-relation predicate on any candidate and refuses a deferred-filter state
Django never writes) is stated in **all five homes**; each edit below is a home that was false or
incomplete against it, and nothing else in the spec was touched. Spec line numbers are from the
file as edited.

- `docs/spec-050-list_field_arguments-0_0_15.md` lines 12-14, the header Revision line — named
  only the evaluation carry as Decision 8's change; the admission is the other half and a reader
  orienting from the header would not find it. **Home 0 (status line), per-spawn duty.**
- Lines 127-132, `## Slice checklist` Slice 3 — the row said "pinned live at Django's own
  manager's count"; "count" alone is an equality claim, which is vacuous, and the row named
  nothing about the admission the live proof needs. Now names the absolute count, the bake, and
  the refusal. **Home 1.**
- Lines 879-884, Decision 5 step 4 — stated "the one subclass that still fails …
  a subclass carrying an unresolved `_deferred_filter` cannot be safely baked and fails closed as
  `untrusted`". Measured false (any class carries one); rewritten to put the failure on the
  STATE's shape. **Home 2.**
- Lines 886-891, same step — "the seal is a rebuild boundary that never copies `_result_cache`"
  was falsified by the carry the prior pass landed and this pass caught it: scoped to the seals
  that recompose, with the raw-list policy named as the exception. **Home 2.**
- Lines 911-915, same step — the enumeration "the `QuerySet.__dict__` fields the seal carries
  forward" changed subject when the carry landed; now says "every seal" and names where the
  carried slot's shape is pinned instead.
- Lines 1246-1268, `### Decision 8` — the subclass paragraph ended at "A subclass that cannot be
  faithfully rebuilt is refused"; nothing said a pending reverse-relation predicate is not that
  case, which is the gap the build pass stalled on. New paragraph states the admission, the bake
  mechanism, the exact-shape refusal including `negate`, and that sealability does not depend on
  which surface seals. **Home 3 (the Decision).**
- Lines 2453-2461, `## Test plan` -> `### Package tier` — said the subclass refusal is "also
  proven live on both public overrides"; that live row now proves the malformed case, so the
  bullet names what each tier pins after the change. **Home 4.**
- Lines 2556-2572, `## Test plan` -> `### The raw-list row source` — harmonized
  `QuerySet.as_manager()` / `Manager.from_queryset` as one shape in one sentence (the two homes
  read as two requirements, flagged in the prior pass's notes and in the build report), and added
  the pending-predicate rows built through Django's own `_apply_rel_filters` rather than
  hand-planted. **Home 4.**
- Lines 2579-2592, same section — the live paragraph asserted only "the query count equal to
  Django's own manager's". Now: two parent cardinalities, an absolute count, the DEFAULT-manager
  mount (the reverse-manager mount proves nothing — measured), the class-entry optimizer (a
  shared plan cache makes the control measure the mounted row), and why the async row asserts
  rows rather than a count. **Home 4.**
- Lines 2795-2810, `## Definition of done`, "No raw-list row source decides its own ceiling" —
  gained the admission and the exact-shape refusal, which is the DoD row that owns them.
  **Home 5.**
- Lines 2817-2821, `## Definition of done`, "A source that arrives evaluated" — "costs the same
  query count" became "returns the same rows at the same ABSOLUTE query count … at two parent
  cardinalities and on both transports", so the row cannot be discharged by a vacuous equality.
  **Home 5.**

- `docs/spec-050-list_field_arguments-0_0_15-rationale.md` `### Decision 8` — added the measured
  fact behind the admission (every relation queryset carries the pending tuple whatever its
  class; all five policies refused the subclass while admitting the exact queryset) and the four
  rejected alternatives: refusing `from_queryset` relations as unsupported, re-querying instead
  of carrying, mounting the proof on the reverse relation manager (a shape that never reaches the
  branch — measured as 2 queries and rows returned, identical to the unmounted control), and
  confining the admission to a `_SealPolicy` axis. Also why `negate` gained its exact-`bool`
  check with the admission.
- Same file, `### Decision 20` — recorded the connection-field separation as a decided
  SEPARATION rather than an omission: `connection.py::_pipeline_sync` / `_pipeline_async` apply
  `FilterSet.apply_*` / `OrderSet.apply_*` with no routing snapshot and no re-seal where
  `list_field.py` does both; the rule broken is that a hook's result contract does not depend on
  which field called it; the row it breaks is `spec-030` Decision 7's "later steps can only
  narrow" upper bound; owner `maintainer` until a card number exists, on a new card owned by the
  connection field rather than a reopening of 050 (Decision 22).

### Plan revision

Written after the build pass set `Status: revision-needed` as the structural-drift pause. The
package tier of the original plan landed, is green and is proven distinguishing; nothing in it is
withdrawn. What this revision adds is the admission fix the pause asked for, its rows, and the
live tier that was unbuildable without it. `Status:` returns to `planned`; the next pass is a
Worker 2 build pass over this subsection plus the untouched live half of the original plan.

#### The measured facts this revision is planned against

Re-derived in this pass rather than carried from the build report, because a plan built on
another pass's numbers is a plan nobody measured. Probes ran from the repository root as
`PYTHONPATH=examples/fakeshop uv run python <scratch>/probe/<name>.py` against a throwaway test
database (`DiscoverRunner.setup_databases`), so the tracked `examples/fakeshop/db.sqlite3` was
never written.

1. **Django leaves a pending `_deferred_filter` on every relation queryset it builds, whatever
   class the manager was made from.** `django/db/models/fields/related_descriptors.py`
   `#"queryset._defer_next_filter = True"` in `_apply_rel_filters` is followed by
   `queryset.filter(**self.core_filters)`, and `QuerySet._filter_or_exclude` stores
   `(negate, args, kwargs)` on `self._chain()` — which preserves the candidate's class. Measured:
   `Branch.shelves.all()` under Django's own manager is an exact `QuerySet` carrying
   `(False, (), {'branch': <Branch: b>})`; the same relation built from a no-override
   `QuerySet` subclass carries the identical tuple on the subclass. So
   `django_strawberry_framework/utils/querysets.py::_seal_or_defect` #"A SUBCLASS leaving a
   predicate pending is not that reverse-relation artifact" states a premise that is false.
2. **Every seal refuses it, not just the raw-list one.** `_seal_or_defect` was called directly on
   that subclass relation queryset under all five shipped policies. `_DEFAULT_SEAL_POLICY`,
   `_LIST_ARGUMENT_VISIBILITY_POLICY`, `_ORDERSET_RESULT_POLICY` (at `f7192bfb`; now `_SIDECAR_RESULT_POLICY`, which also seals `FilterSet.apply_*` returns), `_PREFETCH_CHILD_POLICY` and
   `_RAW_LIST_SOURCE_POLICY` each returned
   `("untrusted", "_ProjectQuerySet carries an unresolved deferred filter")`; the exact queryset
   sealed under all five. The defect is therefore NOT raw-list-local.
3. **It is reachable through the visibility boundary too.** With `Shelf`'s default manager
   mounted from `models.Manager.from_queryset(<no-override subclass>)` (via
   `Shelf._meta.local_managers` + `_meta._expire_cache()`, restored in `finally`),
   `apply_type_visibility_sync(ShelfType, branch.shelves.all(), info=None)` raises
   `ConfigurationError` — `ShelfType` declares a custom `get_queryset`, so this is the
   visibility-rebuild branch, a different path from the one the pause found.
4. **The live control's absolute query count is 2, at both parent cardinalities.** A
   `DjangoSchema` with `extensions=[DjangoOptimizerExtension]` (class entry), a `DjangoListField`
   `patrons` root over `PatronType`, `{ patrons { name loans { note } } }`, seeded 2x3 and 3x3:
   Django's own manager costs **2** queries at cardinality 2 and **2** at cardinality 3 (the
   parent query plus one prefetch), returning `[3, 3]` and `[3, 3, 3]` loans. With `Loan`'s
   default manager mounted from `Manager.from_queryset`, both cardinalities cost 2 queries and
   return `data: None` with the raw-list `ConfigurationError`. This independently reproduces the
   pause and supplies the absolute number L1 asserts.
5. **The mount that reaches the seam is the model's DEFAULT manager, not the reverse relation
   manager's queryset class.** `optimizer/walker.py::_build_child_queryset` seeds the generated
   `Prefetch` from `utils/querysets.py::base_queryset(field.related_model)` and seals that child
   only `if has_custom_qs`; on the no-custom-visibility branch the child is
   `Loan._default_manager.all()` unsealed, and Django's `prefetch_one_level` caches
   `manager._apply_rel_filters(lookup.queryset._chain())`, whose class is the lookup queryset's.
   Mounting `Patron.loans.related_manager_cls` therefore leaves an exact `QuerySet` in the cache
   and proves nothing. This confirms the build report's first measured fact from the other
   direction.

#### Fix shape: the class gate is removed, and the bake's own exact-shape proof is the whole rule

**Chosen.** Delete the two-line exact-`QuerySet` gate in `_seal_or_defect`, so a pending
`_deferred_filter` is resolved for every candidate by `_bake_deferred_filter_or_defect`, and
complete that helper's exact-shape proof with the one slot it does not yet pin (`negate`).

**Why not a `_SealPolicy` axis.** An axis was assessed and rejected. It would confine the fix to
`_RAW_LIST_SOURCE_POLICY` and leave measured fact 3 live — the same project shape, the same
pending predicate, refused at the visibility boundary — which is a knowingly partial fix
(`AGENTS.md` #"Always give the root-cause fix even when slower"). It would also encode "this
state is trustworthy here and untrustworthy there" with **no mechanical difference to justify
it**: every existing axis names a real one (what the rows ARE, whether this surface recomposes,
which connection, whether the surface demanded the result), whereas the bake dispatches no
candidate code and proves the same things whoever calls it. That is the same rule Decision 20's
rationale entry records for the connection field below — a hook's result contract does not depend
on which field called it — read onto sealability. One authoritative definition per rule
(`docs/dry/DRY.md` design principles): the axis would be the second.

**DRY delta over the original `### DRY analysis`, which otherwise stands.**

- **Helper inventory checked.** The package-wide inventory from the original planning pass is
  reused and is current for the shapes this revision needs: the only executable change in
  `django_strawberry_framework/` since it was generated is this cohort's own carry
  (`git diff HEAD --stat` over the package = `utils/querysets.py`, `resource_policy.py`,
  `types/resolvers.py`). Shapes searched for this revision: `deferred`, `bake`, `negate`,
  `add_q`, `_apply_rel_filters`, `PROHIBITED_FILTER_KWARGS`. Relevant candidates, all in
  `utils/querysets.py`: `_bake_deferred_filter_or_defect`, `_deferred_value_defect`,
  `_queryset_state_defect`, `_safe_type_name`, `PROHIBITED_FILTER_KWARGS`. No second bake, no
  second shape-proof helper and no new module is justified.
- **Existing patterns reused.** `_bake_deferred_filter_or_defect`'s own exact-shape block
  (`type(deferred) is not tuple`, `type(kwargs) is not dict`, `type(args) not in (tuple, list)`)
  is the established grammar; the new `negate` check is one more line in it with the same
  `f"{cls_name} deferred filter ... is a {_safe_type_name(...)}"` message shape, and reuses the
  `untrusted` code with no new arm at any message site.
- **Duplication risk avoided.** The naive implementation adds a second admission rule (a policy
  axis) or a second refusal message for "subclass with a deferred filter". Neither is written:
  one gate is deleted, one conjunct is added inside the one helper that already owns the shape
  proof.

**What the observable contract becomes**, and the builder implements exactly this:

- A no-override `Manager.from_queryset` relation source seals, keeps its SQL `LIMIT`, and carries
  its evaluated rows through the raw-list seam — costing the query count Django's own manager
  costs.
- The same source seals at the visibility boundary and at the OrderSet-result seal, because
  sealability does not depend on which surface seals.
- A deferred-filter state that is not the exact shape Django writes — a non-3-tuple, a non-`dict`
  `kwargs`, a non-`tuple`/`list` `args`, a non-`bool` `negate`, a non-`str` kwarg key, a
  prohibited kwarg, a value that is neither inert nor genuine Django, or a predicate `add_q`
  cannot resolve — is still refused with the typed `ConfigurationError`, on every surface.

#### Ownership: three paths the partition does not name (Worker 0 decision needed before dispatch)

The admission change flips the verdict of rows that live outside Cohort A's declared file list.
Every one of them belongs to this change and to no other cohort (Cohort B owns only
`docs/README.md` and `README.md`), so this is a fold-in, not a collision — but
`docs/builder/BUILD.md` `### Parallel cohorts under a declared ownership partition` makes the
re-partition Worker 0's to record in the plan, and a worker never silently writes outside its
cohort. **Worker 0: fold these three into Cohort A before dispatching the build pass.** They are
enumerated, not sampled — `grep -rn "unresolved deferred filter"` plus
`grep -rn "_deferred_filter"` across all four test trees and the package returns exactly these
sites beyond the ones Cohort A already owns:

1. `examples/fakeshop/test_query/test_list_field_api.py` — `#"class _DeferredFilterQuerySet"`,
   `#"def _override_untrusted"`, and the `unresolved-deferred-filter` row of
   `#"_MALFORMED_APPLY_SYNC_ROWS"`.
2. `examples/fakeshop/test_query/test_list_field_async_api.py` — the async twins
   (`#"class _AsyncDeferredFilterQuerySet"`, `#"async def _async_untrusted"`, and its row).
3. `django_strawberry_framework/permissions.py` — one docstring clause in
   `permissions.py #"Query`` class, a foreign row iterable, or an unresolved deferred filter)"`.

The spec itself requires (1) and (2) to exist: `## Test plan` -> `### Package tier` says the
subclass-with-pending-filter refusal is "also proven live on both public overrides". They are
re-pinned, never deleted, and never weakened — see `#### Test additions / updates (revision)`.

If Worker 0 declines the fold-in, this revision does not ship as planned; say so rather than
building a partial fix.

#### Implementation steps (revision)

Steps 1-11 of the original plan already landed. These are additional, and line numbers are
pin-at-write-time hints — verify against current source before editing.

**Before the first edit to any owned file:** `git diff HEAD -- <path>` must show only this
cohort's own landed hunks for the five files it already touched, and nothing for the rest.

**HEAD moved during this planning pass** and the tree is not the one the build report describes.
The concurrent session's `django_strawberry_framework/optimizer/walker.py` change — the
`_UNRECOMPOSED_CHILD_POLICY` -> `_PREFETCH_CHILD_POLICY` swap in `_build_child_queryset` the
build report recorded as dirty — is now **committed and the file is clean**, as are
`docs/TREE.md`, `examples/fakeshop/test_query/README.md`,
`examples/fakeshop/test_query/test_debug_toolbar_api.py` and `tests/middleware/*`. That file is
still in **no** cohort's set: do not edit it. Its committed state is what measured fact 5 above
was read against, so the fact holds at the current HEAD; re-read
`walker.py::_build_child_queryset` before relying on it anyway. Baseline-dirty and out of scope
now: `docs/README.md` (Cohort B), `docs/feedback.md`, `examples/fakeshop/db.sqlite3`,
`docs/bug_hunt/*`.

12. `django_strawberry_framework/utils/querysets.py::_bake_deferred_filter_or_defect` — after the
    `negate, args, kwargs = deferred` unpack and beside the existing `kwargs` / `args` shape
    checks, add `if type(negate) is not bool: return ("untrusted", f"{cls_name} deferred filter
    negate is a {_safe_type_name(negate)}")`. **This is the one new boundary.** Its reason,
    stated in the code as an invariant and not as history: `~predicate if negate else predicate`
    truth-tests the slot, so an object planted there decides whether the predicate is NEGATED —
    the one remaining consumer-dispatch point inside a helper whose whole contract is that it
    runs only genuine Django code over pre-proven arguments. Django writes an exact `bool` there,
    so the refusal is fail-closed on state Django does not produce, exactly as the `tuple` /
    `dict` checks beside it are. Extend the helper's docstring's "malformed shape Django never
    produces" enumeration with it.
13. Same file, `_seal_or_defect`, the deferred-filter arm (~line 3261) — delete
    `if type(candidate) is not models.QuerySet: return None, ("untrusted", f"{cls_name} carries
    an unresolved deferred filter")`, so `_bake_deferred_filter_or_defect` runs for every
    candidate. Rewrite the comment block above it (~line 3251): it currently asserts that Django
    leaves the artifact only on an exact plain `QuerySet` and that a subclass "is not that
    reverse-relation artifact", which measured fact 1 falsifies. The replacement states the live
    rule: `RelatedManager._apply_rel_filters` leaves the `(negate, args, kwargs)` tuple on
    whatever class the model's manager builds, so the predicate is baked onto the detached clone
    the same way for every candidate, through the unbound `sql.Query.add_q` over arguments proven
    inert or genuine Django first, and the candidate's own class decides nothing. Keep the
    `is not None`-never-truthiness paragraph verbatim; it is unaffected and still load-bearing.
14. Same file, `_seal_or_defect`'s docstring `untrusted` enumeration — the clause "a SUBCLASS
    instance carries an unresolved ``_deferred_filter`` -- a predicate not yet baked into the
    query (an EXACT plain ``QuerySet`` carrying one ... is baked ...)" inverts after step 13.
    Rewrite it to: a pending `_deferred_filter` is baked onto the detached clone for every
    candidate, and what fails closed is a deferred-filter STATE that is not the exact shape
    Django writes. Keep every existing sub-clause about the unbound `add_q`, the never-mutated
    candidate, and the typed-not-raw failure; only the subject changes from the candidate's class
    to the state's shape.
15. Same file, `_sealed_prefetch_related_lookups`'s docstring (~line 2413) — "a subclass carrying
    an unresolved deferred filter" in the list of child shapes that fail the outer seal closed
    becomes a malformed deferred filter. One clause.
16. Same file, `_prepared_visibility_source`'s docstring (~line 3710) — "no unresolved deferred
    filter" in the sealable enumeration becomes "a pending deferred filter in the exact shape
    Django writes". One clause.
17. Same file, the `apply_type_visibility` `untrusted` message (~line 3770, `#"unresolved
    deferred filter cannot be faithfully rebuilt"`) — this is consumer-facing error text that
    will now be wrong for the shape it names: a pending deferred filter CAN be faithfully
    rebuilt. Replace that item of the list with a malformed deferred filter. Do not touch the
    other items or the closing "Pass a queryset backed by a plain django.db.models.sql.Query"
    sentence.
18. `django_strawberry_framework/permissions.py` (**pending the fold-in above**) — the same
    correction in the cascade renderer's docstring clause.

#### Test additions / updates (revision)

No `--cov*` flag in any command. Focused runs only; the full sweep belongs to the final gate.

**Package tier — `tests/utils/test_querysets.py`.** The sealer's admission is this file's job, so
the admission half lands here and the relation-shaped rows land live.

- `test_unresolved_deferred_filter_subclass_result_fails_closed` is **flipped, not deleted**. Its
  subject was the class gate, which is gone. Rewritten, it pins the new rule at the same seam
  (`apply_type_visibility_sync` over a subclass hook result): a no-override subclass carrying a
  well-formed `(False, (), {"name": "later"})` now SEALS, the returned object is an exact
  `QuerySet`, and the predicate is in the compiled SQL (assert against
  `sealed.query.get_compiler(using="default").as_sql()`, the idiom
  `test_deferred_filter_never_dispatches_instance_shadowed_inplace` already uses). Rename it to
  state what it pins. Its docstring must not restate the trust levels (shared shape 2).
- **R1 (refusal arm, package)** — parametrized over a SUBCLASS candidate whose deferred-filter
  state is malformed in each of four ways, each asserting the exact `("untrusted", ...)` tuple
  and that no sealed queryset is returned: a non-3-tuple; a non-`bool` `negate` (**the new
  boundary**); a non-`dict` `kwargs`; a value that is neither inert nor genuine Django. These are
  the checks that were unreachable for a subclass before step 13, so they need rows now even
  though only one of them is new code.
- **R2 (the new boundary, exact queryset)** — a non-`bool` `negate` on an EXACT `QuerySet`. This
  path is reachable today and is unpinned at HEAD; without it the `negate` check is pinned only
  through the subclass arm, and the boundary would rest on rows the gate removal created.
- **R3 (no dispatch)** — a `negate` object whose `__bool__` appends to a spy list: the defect is
  returned and the spy never fires. Same shape as
  `test_deferred_filter_never_dispatches_instance_shadowed_add_q`; this is what proves the check
  precedes the truth test rather than merely accompanying it.
- Every existing exact-`QuerySet` deferred-filter row in this module stays byte-identical. They
  are the controls that prove the gate removal changed nothing on the common path, and the build
  report must say so.

**Package tier — `tests/test_resource_policy.py`.** The seven P/B rows from the original plan
stay as built. Add one:

- **P6** — a no-override `QuerySet` subclass carrying a relation-shaped pending deferred filter
  (built by calling `<parent>.<relation>._apply_rel_filters(<subclass>(model=...))`, Django's own
  machinery, never a hand-planted tuple) through `bounded_rows`: rows equal the leading window,
  the returned rows are the relation's rows, and the SQL the rebuild compiles carries the
  relation predicate. This is the package-tier statement of the contract the live rows prove over
  the wire, and it uses Django to produce the state so the row cannot drift from what Django
  actually writes.

**Live tier — `examples/fakeshop/test_query/test_resource_policy_api.py`.** Everything the
original plan's live section asked for, with the mount corrected by measured fact 5.

- **The mount.** A context manager replacing `Loan`'s DEFAULT manager with
  `models.Manager.from_queryset(<a module-level no-override QuerySet subclass>)()`, by assigning
  `Loan._meta.local_managers` and calling `Loan._meta._expire_cache()`, restoring both in
  `finally`. Verified working end to end in this planning pass (measured fact 4: the mounted run
  reached `normalized_row_source` and the unmounted run did not). `examples/fakeshop/apps/library/models.py`
  stays unedited, so the plain-manager control remains the same relation, the same document and
  the same seed with the mount simply absent (superseded by P2-2: `Loan` declares `objects = LoanQuerySet.as_manager()`) — the control argument in
  `### Why the Manager.from_queryset shape is mounted at the probe, not declared on a model`
  stands unchanged and is not re-argued here.
- **The probe schema.** A `DjangoSchema` over a `DjangoListField` `patrons` root, built in the
  idiom of `#"def _hostile_relation_schema"` (type-as-argument, keyed cache, real annotation
  object under `from __future__ import annotations`), with its own `max_list_rows` — but with the
  optimizer installed as a **class entry**, `extensions=[DjangoOptimizerExtension]`. Class rather
  than the fakeshop singleton-in-a-factory spelling for a measured reason: the plan cache lives
  on the extension INSTANCE and holds the generated `Prefetch`, hence its child queryset object,
  across requests, so a shared instance would make the control measure the mounted row's class
  (the build report's fourth note). A class entry gives each operation its own plan cache, which
  is what makes the control a control. Both spellings are the documented class-or-factory
  contract (Decision 21), so this does not contradict Cohort B's recipe — shared shape 1 is
  honoured: `DjangoSchema`, never a plain `strawberry.Schema`, never a bare extension instance.
  Two mounts beside `rp-hostile-relation/`, sync and async.
- **L1 — the load-bearing row**, parametrized over **two parent cardinalities** (2 and 3 patrons,
  3 loans each), running `{ patrons { name loans { note } } }` over the sync mount once with the
  `Manager.from_queryset` mount active and once without. Asserts, in this order: the payload is
  identical between the two runs (same loans, same order); the two query counts are equal; and
  each is the **absolute 2** — one parent query plus one prefetch. The absolute number is
  measured, not guessed: this pass recorded 2 at both cardinalities for the control against a
  real schema (measured fact 4). **Worker 2 re-derives it** from its own run and reports the
  reading; if it differs from 2, the plan's number is what is wrong and the measured one is what
  the row asserts. Equality alone would be vacuous and the second cardinality is what
  distinguishes a prefetch from an N+1 (`BUILD.md` `### Query-shape tests must pin the
  load-bearing property, not observability`).
- **L2 — the async transport.** The same document over the `AsyncDjangoGraphQLView` mount with
  the mount active, asserting the same rows as the sync mounted run. **Instrument warning stands
  and is not waived:** `CaptureQueriesContext` binds to the calling thread's connection and the
  async path runs its ORM work through `sync_to_async` worker threads, so an empty capture reads
  exactly like a green zero. Assert rows only, or assert a count only alongside an absolute
  non-zero control taken by the same instrument in the same row. Whichever is chosen, the build
  report states which and why.
- **L3 — the refusal arm, live, both transports.** The `unresolved-deferred-filter` rows in
  `test_list_field_api.py` and `test_list_field_async_api.py` are re-pinned rather than deleted:
  the override keeps returning a subclass, but with a deferred-filter state Django never writes
  (a 2-tuple, or a non-`bool` `negate`), so the row still proves an `apply_*` override returning
  an untrusted queryset fails closed with the `untrusted` defect through the public sync and
  async overrides. Only the id, the planted state and the asserted substring change; the
  surrounding table, the message prefix and the `resolver_queries` expectation stay. The class
  docstrings (`#"Django leaves a ``_deferred_filter`` only on an EXACT plain queryset"`) carry
  the falsified premise and are rewritten to name what the class now stands for. This is the
  faithful re-pin `BUILD.md` `### Test staleness a focused run cannot see` requires — the row's
  original intent against the current contract, never an assertion weakened to force a pass.
- The module docstring's "Row groups" enumeration
  (`#"the collection bounds the fields enforce"`) gains the prefetched-relation cost group, as
  the original plan says; the docstring is the authoritative description of the suite.

**Full-sweep obligation.** The admission widening changes a seal verdict reachable from four
policies, so the build pass owes the full parallel `uv run pytest --no-cov` (as the prior pass
ran for the carry), not a focused run — a stale row in a tree this plan does not name is exactly
what a focused run cannot see.

**Temp tests for Worker 3:** the probes this pass wrote (`<scratch>/probe/scope.py`,
`vis.py`, `count.py`) reproduce measured facts 2, 3 and 4 without touching the tree; a scratch
row under `docs/builder/temp-tests/050/row_carry/` that mounts the manager and asserts the
control's count is the cheapest check that L1 is distinguishing.

#### Boundary count, failability, and the split question

**One** new boundary: the exact-`bool` `negate` refusal (step 12). The gate deletion (step 13) is
an admission WIDENING — it says no to nothing — and the docstring and message corrections say no
to nothing either. One boundary is one mutate / run / count / revert / byte-compare loop on top
of the widening's own measurement, so **the cohort is still not split**; the admission fix, its
rows and the live tier it unblocks are one contract and would review worse apart.

- **The new boundary owes a full proof.** Mutation: replace the `type(negate) is not bool` check
  with `if False:`. Expected failing rows: R2 (exact queryset), the `negate` case of R1
  (subclass), R3 (no dispatch), and the live L3 rows if they plant a non-`bool` `negate` — at
  least three, above the weakly-pinned threshold. Record the node-id list, the scope as run, the
  pre-mutation state of that scope, 0 collection/setup errors, and the byte-compared revert.
- **The widening owes a distinguishing measurement**, recorded beside the boundary entry as the
  carry's was. Mutation: restore the deleted class gate. It must fail **at least two rows per
  tier** — the flipped `tests/utils/test_querysets.py` row and P6 in the package tier, and both
  parametrized cases of L1 plus L2 in the live tier. A widening only one row can see is
  indistinguishable from one nobody asked for.
- **Controls that must stay silent** under both mutations: every existing exact-`QuerySet`
  deferred-filter row in `tests/utils/test_querysets.py`. Their silence is what proves the change
  isolates the subclass path, and the build report states it.

#### Hot-path budget (revision)

Still declared hot-path; the declared number is unchanged (the query count for one prefetched
`Manager.from_queryset` relation, before and after, beside Django's own manager on the same
document and the same seed, at the larger parent cardinality). Two corrections:

- **"Before" is a refusal, not a cost**, and is recorded as such. The honest before/after pair is
  the MOUNTED relation's count against the plain-manager control's on the same request shape:
  control 2 / mounted `ConfigurationError` before, control 2 / mounted 2 after.
- **A query count cannot see this change's actual added cost**, which is CPU: the bake plus the
  post-bake `_combined_query_table_defect` re-walk now runs for a subclass relation source, and
  `normalized_row_source` runs once per parent row on the many-side branch. An exact-`QuerySet`
  relation already pays exactly that walk today, so the parity claim is the point — but it has to
  be measured, not asserted. **Add one proxy number**: a wall-clock median over a stated
  iteration count for the L1 document at the larger cardinality, mounted versus control, same
  instrument both times. `BUILD.md` `## Hot-path budget` accepts a proxy named at plan time; a
  single-shot reading is not a number.

#### Floor verification (revision)

Unchanged in scope and owner — this build pass, the two package modules, with the full
twenty-three-path scope (the floor at `f7192bfb`; 27 at HEAD) staying the final gate's. Versions and recipe from
`docs/builder/BUILD.md` `## Floor verification` at run time, never from a number restated here.
One addition: `_apply_rel_filters` is the seam the whole revision turns on and its body differs
between the shared `.venv`'s Django and the floor's, so the floor run's scope gains
`tests/test_resource_policy.py` and `tests/utils/test_querysets.py` as before **and** the build
report states that the pending-`_deferred_filter` rows passed at the floor. Never install into
the shared `.venv`.

#### Implementation discretion items (revision)

Assessed and decided to be Worker 2's, in addition to the original list:

- The names of the mounted manager, the no-override subclass and the mount context manager in
  each module, and whether the mount is a `@contextmanager` or a fixture.
- Whether the flipped `tests/utils/test_querysets.py` row asserts the baked predicate through
  `as_sql()` params or through a compiled-SQL substring, provided it asserts the predicate is
  present rather than only that the seal returned something.
- The exact parametrization ids of R1 and of the re-pinned live rows.
- Whether L3 plants a 2-tuple or a non-`bool` `negate`, provided both transports plant the same
  shape and the asserted substring names it.
- The wording of every docstring and comment listed above, within the contract each step states.

#### Spec slice checklist

Both boxes stay `- [ ]`. The package half of each landed in the prior pass; the live half is what
this revision plans. Worker 2 ticks a box only when both halves are in its diff.

---

## Build report (Worker 2)

**Pause (`Status: revision-needed`), and which pause it is:** the
plan-vs-implementation **structural-drift pause** of `docs/builder/worker-2.md`
`## Plan-vs-implementation drift`, routing to Worker **1**, not back to Worker 2. The package
tier of the plan landed in full and is green; the plan's LIVE tier cannot be built as written,
for a reason the plan did not scope and that is a plan-level architectural call, not a
builder's: **under a prefetching plan a `Manager.from_queryset` relation source is REFUSED by
`_seal_or_defect` before the carry is ever reached**, because Django's
`RelatedManager._apply_rel_filters` leaves a pending `_deferred_filter` on it and the seal bakes
that artifact for an EXACT `QuerySet` only. Evidence, mechanism and the two open decisions are
in `### Notes for Worker 1 (spec reconciliation)` below. Nothing is left mutated and no owned
file is half-edited.

### Precondition

`git diff HEAD -- <path>` printed zero lines for every one of the cohort's eleven owned paths
(nine code paths before the fold-in) before the first edit (the concurrent DRY cycle names `utils/querysets.py`; it had not touched
it). Checked as one loop over the ownership list; all clean, so the plan's stop condition did
not fire.

### Files touched

Grounded in `git status --short`, not memory. Exactly five paths, all in the cohort's writable
set:

- `django_strawberry_framework/utils/querysets.py` - plan steps 1 and 3 through 9: the
  `carry_result_cache` axis on `_SealPolicy` with its docstring bullet; `_RAW_LIST_SOURCE_POLICY`
  turning it on and its comment rewritten from "a discarded result cache and one more query" to
  the carry; the new exact-`list` refusal in `_seal_or_defect` (placed immediately BEFORE the
  `require_unevaluated` check so the reused `untrusted` code keeps its fixed position ahead of
  `evaluated`); the carried assignment in the state-copy block beside `_iterable_class`; the
  `untrusted` docstring enumeration gaining the `_result_cache` shape clause;
  `normalized_row_source`'s closing paragraph; `materialized_rows`'s docstring reading the
  exact-type rule as the reason it is correct; and `_prepared_visibility_source`'s cached-rows
  clause scoped to this seal's policies.
- `django_strawberry_framework/resource_policy.py` - plan step 10: one docstring paragraph on
  `_windowed_rows`. No code change.
- `django_strawberry_framework/types/resolvers.py` - plan step 11: the many-side resolver's
  prefetched-path comment corrected. No code change.
- `tests/test_resource_policy.py` - the P and B rows below, the `_ProjectQuerySet` /
  `_LyingResultCache` / `_evaluated` / `_held_rows` scaffolding, and the reworded docstring of
  `test_a_queryset_subclass_is_never_asked_what_it_has_already_fetched` (its assertion is
  byte-identical).
- `tests/utils/test_querysets.py` - the sealer-admission rows.

`examples/fakeshop/apps/library/models.py` is unedited, as the plan says (superseded by P2-2: `Loan` declares `objects = LoanQuerySet.as_manager()`). The three live
`examples/fakeshop/test_query/*.py` files the cohort owns are also unedited - see the pause.

### Tests added or updated

Package tier, `tests/test_resource_policy.py` (beside the existing raw-list-source rows):

- `tests/test_resource_policy.py::test_an_evaluated_exact_queryset_is_windowed_from_the_rows_it_holds`
  (P1) - zero queries, rows equal to AND the same objects as the leading window the source held.
- `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds`
  (P2) - zero queries; the rebuild happened (`type(normalized_row_source(source)) is QuerySet`);
  the rebuild carries the source's own list (`materialized_rows(rebuilt) is held`); rows by
  identity.
- `tests/test_resource_policy.py::test_a_coordinate_window_over_an_evaluated_project_queryset_class_reads_carried_rows`
  (P5) - the `offset=1, requested_limit=2` window over the carried rows, zero queries, rows by
  identity.
- `tests/test_resource_policy.py::test_an_evaluated_exact_queryset_is_windowed_from_its_own_rows_when_awaited`
  (P4) and
  `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited`
  (P3) - the same two shapes through `bounded_rows_async`.
- `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_rather_than_carried`
  (B2) and
  `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_when_awaited`
  (B3) - a lying sequence in the cache slot, typed `ConfigurationError` naming the shape, and the
  liar's rows never reach the caller.

Package tier, `tests/utils/test_querysets.py` (beside `test_seal_require_unevaluated`, which is
unchanged - it builds `_SealPolicy` by keyword, so a new defaulted field does not reach it):

- `tests/utils/test_querysets.py::test_seal_carry_result_cache_carries_the_rows_the_source_holds`
  (B1, the admission half) - the source's own list object travels onto the sealed queryset, and
  the same source under `_DEFAULT_SEAL_POLICY` seals to `_result_cache is None`.
- `tests/utils/test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list[list-subclass]`,
  `[tuple]`, `[foreign-object]` (B1, the refusal half) - the `("untrusted", "<class>._result_cache
  is a <type>")` defect and no sealed queryset. Every case is EMPTY or falsy, so the rows also pin
  that the refusal keys on the slot being populated rather than on truthiness.

**The query-count instrument, stated.** The sync rows use `django_assert_num_queries(0)` - the
absolute zero, never an equality. The two async rows do NOT assert a count: a
`CaptureQueriesContext` opened on the event-loop thread cannot see ORM work a `sync_to_async`
worker thread would do, so an empty capture there is indistinguishable from a green zero. They
assert **row identity** against the list the source already holds instead, which is strictly
stronger for the question being asked - a second fetch cannot return the objects the source is
already holding - and the plan licenses exactly this substitution. P5 carries the same identity
assertion for a second reason recorded in `### Implementation notes`.

### Validation run

- `uv run ruff format <the five files>` - pass (1 file reformatted:
  `utils/querysets.py`, where the new `untrusted` return was exploded across lines).
- `uv run ruff check --fix <the same five files>` - pass, "All checks passed!".
- `uv run python scripts/check_trailing_commas.py --check <the same five files>` - pass (explicit
  paths, never bare).
- `git status --short` after both ruff invocations - the five paths above plus, unchanged by this
  pass, the plan's recorded baseline-dirty set and the concurrent cohorts' files
  (`docs/README.md` is Cohort B's, `docs/GLOSSARY.md` / `docs/TREE.md` / `docs/bug_hunt/*` /
  `docs/dry/*` / `docs/feedback.md` / `examples/fakeshop/db.sqlite3` /
  `examples/fakeshop/test_query/README.md` / `examples/fakeshop/test_query/test_debug_toolbar_api.py`
  / `tests/middleware/*` / `tests/test_export_dry_review.py` are concurrent work, and
  `docs/spec-050-...-rationale.md` and `docs/builder/DONE/build-050-...` are Worker 1's and Worker
  0's). **Nothing outside the cohort's writable set was edited or reverted.**
- `uv run pytest -n0 tests/test_resource_policy.py tests/utils/test_querysets.py --no-cov -q` -
  **615 passed**.
- `uv run pytest --no-cov -q` (the full parallel sweep across all four trees, owed because the
  carry changes what `bounded_rows` RETURNS for an evaluated queryset - Django answers a
  populated-cache subscript with a `list`, where an unevaluated queryset answers with a sliced
  queryset) - **8323 passed, 39 skipped** in 137s, exit 0. No stale tree.
- `uv run python scripts/check_citations.py --check` - pass, 1101 citations resolve.
- ASCII check over the five files - 0 non-ASCII bytes in each.

**Stop-and-report, not a revert.** `django_strawberry_framework/optimizer/walker.py` was CLEAN in
the `git status --short` this pass took after its ruff runs and is dirty in the one it took at the
end: 21 insertions, 5 deletions swapping `_UNRECOMPOSED_CHILD_POLICY` for
`_PREFETCH_CHILD_POLICY` in `_build_child_queryset` with its comment rewritten. This pass did not
write that file, it is in no cohort's writable set, and it has not been touched or reverted -
recorded here so a later pass does not read it as this cohort's churn. Timing worth having: the
file was still clean when the full sweep was ~94% through, so the sweep's collection read the
version without those hunks, and **the 8323-passed figure above does not cover them**. It is also
the same module whose `_build_child_queryset` supplies the prefetch child the pause below turns
on, so whoever owns that edit should see the pause and vice versa.

### Failability proofs

Produced by `uv run python scripts/prove_failability.py
docs/builder/temp-tests/050/row_carry/proofs.json --scratch-root <scratch>/proofs`, exit **0**,
re-run after `ruff format` so the recorded anchors and hashes describe the shipped bytes. Both
entries carry a green pre-mutation baseline (`615 passed`, pytest exit 0) and **0**
collection/setup errors, so both counts are valid counts.

- `django_strawberry_framework/utils/querysets.py::_seal_or_defect` (**the one new boundary**) -
  mutation applied: the line `if policy.carry_result_cache and result_cache is not None and
  type(result_cache) is not list:` replaced by `if False:`, so a populated cache Django never
  built is carried onto the rebuild and answers the window with its own `__getitem__`; scope as
  run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE
  tests/test_resource_policy.py tests/utils/test_querysets.py`; pre-mutation state of that scope:
  green (`615 passed`, exit 0), 0 pre-existing failing rows differenced out; failing node ids:
  `tests/utils/test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list[list-subclass]`,
  `tests/utils/test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list[tuple]`,
  `tests/utils/test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list[foreign-object]`,
  `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_rather_than_carried`,
  `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_when_awaited`;
  collection/setup errors: 0 (a valid count); revert proved by byte comparison:
  `filecmp.cmp(shallow=False)` True and sha256 `50091053a741df5b...` == `50091053a741df5b...`
  against the pre-mutation copy. Five rows, so not weakly pinned.
- `django_strawberry_framework/utils/querysets.py::_RAW_LIST_SOURCE_POLICY` (**the carry itself -
  not a refusal boundary, but not only a cost: it refuses nothing**, recorded here because the plan requires
  the carry's own rows to be distinguishing) - mutation applied: `carry_result_cache=True,`
  replaced by `carry_result_cache=False,`; scope as run and pre-mutation state: identical to the
  entry above; failing node ids:
  `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds`,
  `tests/test_resource_policy.py::test_a_coordinate_window_over_an_evaluated_project_queryset_class_reads_carried_rows`,
  `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_rather_than_carried`,
  `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited`,
  `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_when_awaited`;
  collection/setup errors: 0; revert proved by byte comparison as above. That is **three P rows
  across both colors** (the two B rows fail because a policy that carries nothing never reaches
  the refusal), meeting the plan's "at least two rows per tier" for the package tier. The LIVE
  tier's half of that requirement is NOT met and is part of the pause. (Discharged at `ae52bdec`:
  under the mutation L1 fails at both cardinalities, `assert 4 == 2`, and L2 fails, `data` None.)

The plan's exact-queryset rows (P1 sync, P4 awaited) are deliberately unaffected by the carry
mutation: `normalized_row_source` returns an exact queryset unchanged without sealing it, so the
common shape already cost nothing. They are controls, and their silence under the mutation is the
evidence that the mutation isolates the subclass path.

### Hot-path budget

The plan declares this cohort hot-path and names the number: the query count for a prefetched
`Manager.from_queryset` relation, before and after, beside Django's own manager on the same
request shape. Both readings were taken with the same instrument
(`django.test.utils.CaptureQueriesContext(connection)`), the same seed and the same document;
"before" was taken by the `BUILD.md` fenced loop (anchor asserted to match exactly once, copy to
`<scratch>/dsf-hotpath-before.orig`, mutate `carry_result_cache=True,` -> `False,`, run, restore,
`cmp` exit 0). A query count is reproducible, so no iteration statistic is needed.

Command (both readings):

```shell
uv run pytest -n0 docs/builder/temp-tests/050/row_carry/test_hotpath.py --no-cov -q -s
```

| Metric | Before | After | Delta |
|---|---|---|---|
| Live `patrons { name loans { note } }` under a prefetching plan, **Django's own manager** (the control), 2 parents x 3 loans | 2 | 2 | 0 |
| Same document, same control, 3 parents x 3 loans | 2 | 2 | 0 |
| Same document, relation sourced from a **`Manager.from_queryset` class with no overrides**, 2 and 3 parents | 2, **request REFUSED** | 2, **request REFUSED** | unchanged |
| The raw-list seam itself, one **evaluated exact `QuerySet`** through `bounded_rows` (control) | 0 | 0 | 0 |
| The raw-list seam itself, one **evaluated project queryset class** through `bounded_rows` | 1 | **0** | **-1 per source** |

Read honestly: **the carry removes exactly the query it was specified to remove** - one per
evaluated subclass source, which on the many-side relation branch is one per parent row - and the
exact-queryset control confirms the common shape pays nothing either way. The
`Manager.from_queryset` live row's count is **not** a cost comparison at all: at both readings
the request errors out with the typed `ConfigurationError` from the seal's deferred-filter arm,
so its two queries are the parent query plus the optimizer's prefetch, with the relation field
never delivering rows. That row is the pause, not a measurement, and the number is recorded as
what it is rather than laundered into a passing equality.

### Floor verification

The plan assigns this pass the two package modules; the full twenty-three-path scope (the floor at `f7192bfb`; 27 at HEAD) stays the
final gate's. Versions and recipe copied from `docs/builder/BUILD.md` `## Floor verification` at
run time, never from memory.

- scratch venv (outside the repo): `<scratch>/dsf-floor`, built with
  `uv venv <scratch>/dsf-floor --python 3.10`, then
  `uv pip install --python <scratch>/dsf-floor/bin/python -e . --group dev` and
  `uv pip install --python <scratch>/dsf-floor/bin/python 'django==5.2.16'
  'strawberry-graphql==0.316.0'`. The explicit `--python` is what keeps it out of the shared
  `.venv`.
- resolved versions, as read by `uv pip list --python <scratch>/dsf-floor/bin/python`:
  `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 25.2`,
  `django-strawberry-framework 0.0.15` (editable, this checkout), `pytest 9.1.1`; interpreter
  `3.10.19`.
- scope as run:
  `<scratch>/dsf-floor/bin/python -m pytest tests/test_resource_policy.py
  tests/utils/test_querysets.py --no-cov -q -p no:cacheprovider` - **611 passed, 4 skipped**,
  pass. (The four skips are the `Schema.stream` rows the module skips below
  strawberry-graphql 0.319.0, which is the floor behaving as the suite declares.)
- shared `.venv` unmutated: `uv pip list` in the repo read `django 6.1`,
  `strawberry-graphql 0.324.0`, `django-filter 26.1` **before and after** the floor run, the same
  three readings both times.

### Implementation notes

- **The carry is one more slot in the sealer, not a write in `normalized_row_source`.** Built
  exactly as the plan's DRY analysis prescribes: the axis is a field on `_SealPolicy`, the read is
  the same `state.get(...)` every other retained slot comes from, and the assignment sits beside
  `sealed._iterable_class`. Validation and execution therefore still provably consume one
  extraction, which is the property `_seal_or_defect`'s own docstring claims.
- **The list object travels; it is not copied.** An O(n) copy per rebuilt subclass would be a
  per-parent-row cost on the branch the carry exists to make cheap, the row objects are shared
  either way, and `QuerySet` hands its own cache out uncopied everywhere else. The sealer's
  `_known_related_objects` drop and its comment are untouched.
- **`type(...) is list`, not `isinstance`.** A `list` subclass brings its own `__getitem__`, and
  `QuerySet.__getitem__` returns `self._result_cache[k]` once the cache is populated, so carrying
  a subclass would put the raw-list ceiling back inside consumer code. The `[list-subclass]`
  parametrization is that case, and it is the one whose absence the mutation proof would not
  otherwise distinguish from the `tuple` case.
- **`_prefetch_done` is deliberately NOT carried.** Setting it would be a second claim about the
  source (that its nested prefetches are complete) on state the seal has not validated, and it is
  unreachable in this seam: `_bounds_by_its_own_slice` is true for the rebuilt exact queryset, so
  the window is always `result[start:stop]`, and `QuerySet.__getitem__` on a populated cache
  returns `self._result_cache[k]` without ever entering `_fetch_all`. If a later surface iterates
  a carried rebuild instead of subscripting it, that is the decision to revisit - recorded for
  Worker 3 as a thing to look at rather than an invariant asserted here.
- **Small drift the plan will want to see: an evaluated source's window is a `list`, not a
  `QuerySet`.** The plan's P2 asks for "the returned object is an exact `QuerySet` (the rebuild
  happened)". After the carry that is false for a REASON, not by accident: Django answers a
  subscript on a populated cache with `self._result_cache[k]`, so `bounded_rows` on an evaluated
  source returns a plain list at both tiers and for both the exact and the rebuilt shape alike.
  The rows therefore pin the rebuild where it is observable - `type(normalized_row_source(source))
  is QuerySet` and `materialized_rows(rebuilt) is held` - rather than asserting a return type the
  carry necessarily changes.
- **P5 needed identity, not a count.** With the carry removed, `_windowed_rows` returns a LAZILY
  sliced queryset, so the zero-query assertion holds on both trees and the row was
  non-distinguishing when first written (the first proof run measured it: 4 rows, not 5). Row
  identity against the source's own list is what distinguishes them, and the second proof run
  records the corrected 5.
- The new probe module and the measurement module under
  `docs/builder/temp-tests/050/row_carry/` are scratch, not tests: `test_measure.py` (which
  established the mount mechanics reported below), `test_hotpath.py` (the budget readings) and
  `proofs.json` (the manifest). Named `row_carry/` per this pass's task contract; the plan's text
  says `close-row_carry/`. Deleted by explicit path at closeout.

### Notes for Worker 3

- The diff is five files; `resource_policy.py` and `types/resolvers.py` are **prose only** and owe
  the inverse proof shape (`START.md` "Instruments that lie"): their executable tokens are
  unchanged, which `git diff` shows directly - every changed line in both files is inside a
  docstring or a comment.
- `scripts/review_inspect.py` was NOT re-run this pass: Worker 1's plan already ran it on
  `utils/querysets.py` and recorded the overview path, and this pass added 12 executable lines to
  that file plus none to the other two. Recorded as a skip with the reason rather than left
  silent.
- The two async package rows assert no query count on purpose; the reasoning is in
  `### Tests added or updated` and in the rows' own docstrings. If you re-run the failability
  subset, re-run at the scope recorded above and compare node-id SETS: the scope is both package
  modules together, and a narrower one moves the counts.
- The live tier is untouched. Do not read that as an omission: it is the pause below, and the
  evidence for it is reproducible with
  `uv run pytest -n0 docs/builder/temp-tests/050/row_carry/test_measure.py::test_probe_isolated
  --no-cov -q -s`.

### Notes for Worker 1 (spec reconciliation)

**1. The blocker (why the live tier is unbuilt), with its evidence.**

Measured, not reasoned - `docs/builder/temp-tests/050/row_carry/test_measure.py::test_probe_isolated`,
one fresh `DjangoOptimizerExtension` per mount so no plan cache carries a child queryset between
rows:

| Mount | Class the prefetch cache holds | Queries | Result |
|---|---|---|---|
| none (Django's own manager) | `QuerySet` | 2 | rows returned |
| the model's default manager built from `Manager.from_queryset(<no-override QuerySet subclass>)` | `_ProjectLoanQuerySet` | 2 | **`ConfigurationError`**, field errors |
| the reverse relation manager's queryset class (the plan's named mount) | `QuerySet` | 2 | rows returned - the mount never reaches the seam |

Two separate facts, each fatal to the plan's live row on its own:

- **The plan's mount site is inert for a planned prefetch.** `optimizer/walker.py` builds the
  generated `Prefetch`'s child from `utils/querysets.py::base_queryset(field.related_model)`,
  i.e. `Loan._default_manager.all()` - not from the reverse relation manager. Django's
  `prefetch_one_level` then caches `manager._apply_rel_filters(lookup.queryset)`, whose class is
  the LOOKUP queryset's. So mounting `Patron.loans.related_manager_cls` leaves an exact `QuerySet`
  in the cache and the row proves nothing. The site that does reach it is the model's default
  manager - which is the shape the DoD names (`Manager.from_queryset` behind a model's manager)
  and which a test can mount for the duration of one row without touching
  `examples/fakeshop/apps/library/models.py`, so the plan's control argument
  (`### Why the Manager.from_queryset shape is mounted at the probe, not declared on a model`) is
  fully preserved: same relation, same document, same seed, mounted or not.
- **With the mount corrected, the source is REFUSED, not merely re-queried.**
  `RelatedManager._apply_rel_filters` sets `_defer_next_filter` and the `.filter(**core_filters)`
  that follows leaves a pending `_deferred_filter` `(False, (), {'patron': <Patron: ...>})` on the
  cached queryset. `utils/querysets.py::_seal_or_defect` bakes that artifact for an EXACT plain
  `QuerySet` and fails a SUBCLASS closed:
  `#"carries an unresolved deferred filter"`. Every `Manager.from_queryset` relation source
  therefore reaches the raw-list seam unsealable - prefetched or not, since the unprefetched
  branch's `getattr(root, accessor).all()` carries the same artifact. **This is true at HEAD, not
  caused by this pass**: the carry is downstream of the refusal.

So the DoD row "a relation whose manager is a `Manager.from_queryset` class with no overrides
costs the same query count as Django's own manager, proven live under a prefetching plan" is
unreachable today, and so is Decision 8's own claim that "a sealable project subclass therefore
keeps its `LIMIT` in SQL instead of being demoted to a counted Python truncation" for the
relation case. Decision 20 names `a Manager.from_queryset class is standard Django` as guarded
application code, which makes this a contract-level gap rather than a hostile shape.

The architectural call is Worker 1's (and possibly the maintainer's), which is why this pass
paused rather than deciding. The two shapes I can see:

- extend the deferred-filter bake to a SUBCLASS candidate - note the bake already runs over
  arguments proven inert / genuine-Django and uses the UNBOUND `sql.Query.add_q`, never the
  candidate's own methods, so the exact-type gate may be stricter than its own stated reason
  requires; or
- let the raw-list policy alone admit the bake, as a new `_SealPolicy` axis beside
  `carry_result_cache`, leaving every visibility seal's rule exactly as it is.

Either is a new boundary with its own proof and its own rows, and either changes text in
`## Architectural decisions` Decision 8. **Amendment, so this is not a complaint:**

- where it lives: `docs/spec-050-list_field_arguments-0_0_15.md`, `### Decision 8 - queryset and
  iterable sources have explicit, different capabilities`, the paragraph beginning "A `QuerySet`
  SUBCLASS is the one shape that is neither sliced as itself nor counted."
- current wording, quoted: "A subclass that cannot be faithfully rebuilt is refused with a typed
  `ConfigurationError`; the fallback is never its own `__getitem__`."
- recommended replacement: "A subclass that cannot be faithfully rebuilt is refused with a typed
  `ConfigurationError`; the fallback is never its own `__getitem__`. A pending reverse-relation
  predicate is not that case: Django's related-manager machinery leaves one on every relation
  queryset it builds, whatever class the model's manager is made from, so the rebuild resolves it
  through the same unbound `Query.add_q` bake it already runs for an exact queryset rather than
  refusing the project queryset class Decision 20 names as standard Django."

**2. The plan's P2 return-type expectation is falsified by Django's own subscript**, not by an
implementation choice - see the drift bullet in `### Implementation notes`. No spec text states
the return type, so I believe no spec edit is owed; the plan's `### Test additions / updates`
bullet is what should be re-read against the shipped rows.

**3. `docs/GLOSSARY.md` "Sealed execution queryset" is now falsified**, exactly as the plan
predicted: its body states that "`_result_cache` / `_known_related_objects` are never copied
forward". After this pass that is true of every policy except `_RAW_LIST_SOURCE_POLICY`. The
glossary is DB-backed and in no cohort's writable set, so this pass did not touch it. It still
has no owner.

**4. Not a finding, recorded because it surprised me and a later reader will hit it too:** the
optimizer's plan cache holds the generated `Prefetch` object, hence its child queryset object,
across requests. Any live row that mounts a manager for the duration of one request and shares a
`DjangoOptimizerExtension` instance with an unmounted control row measures the FIRST row's class
in both. The isolated probe above is only trustworthy because each mount got its own extension
instance. A live row built later owes the same isolation, or its control is not a control.

---

## Build report (Worker 2, pass 2)

Builds the plan's `### Plan revision`. The package tier of pass 1 is untouched and still green;
what lands here is the admission fix (steps 12-18), its rows, and the live tier the fix unblocks.

### Precondition

Checked as one loop over the ownership list before the first edit:

- The three paths folded in at the revision - `examples/fakeshop/test_query/test_list_field_api.py`,
  `examples/fakeshop/test_query/test_list_field_async_api.py`,
  `django_strawberry_framework/permissions.py` - each printed **zero lines** for
  `git diff HEAD -- <path>`. So did `examples/fakeshop/test_query/test_resource_policy_api.py`,
  `examples/fakeshop/test_query/test_library_api.py`,
  `examples/fakeshop/test_query/test_relations_async_api.py` and
  `examples/fakeshop/apps/library/models.py`.
- The five files pass 1 touched carried exactly pass 1's diff and nothing else, compared against
  that report's `### Files touched`. No foreign hunk.
- `django_strawberry_framework/optimizer/walker.py` is clean, as the revision records. It is in no
  cohort's set and was not touched.

### Files touched

Grounded in `git status --short`, not memory. Nine paths, all in the cohort's writable set as
widened; the four beyond pass 1's five are new this pass.

- `django_strawberry_framework/utils/querysets.py` - revision steps 12 through 17.
  `_bake_deferred_filter_or_defect` gains the exact-`bool` `negate` check beside the existing
  `kwargs` / `args` shape checks, with its docstring's malformed-shape enumeration extended;
  `_seal_or_defect`'s two-line exact-`QuerySet` class gate is deleted so the bake runs for every
  candidate, and the comment block above it is rewritten onto the live rule (the related-manager
  machinery leaves the tuple on whatever class the model's manager builds, the predicate is baked
  onto the detached clone through the unbound `sql.Query.add_q`, the candidate's class decides
  nothing); the `is not None`-never-truthiness paragraph is kept verbatim; `_seal_or_defect`'s
  docstring `untrusted` enumeration moves its subject from the candidate's CLASS to the pending
  STATE's shape and names every refused shape including `negate`;
  `_sealed_prefetch_related_lookups`, `_prepared_visibility_source` and the
  `apply_type_visibility` `untrusted` message each swap "unresolved deferred filter" for the
  malformed one. Pass 1's carry hunks are unchanged.
- `django_strawberry_framework/permissions.py` - revision step 18: the same one-clause correction
  in the cascade's `untrusted` renderer docstring. No code change (as committed in `f7192bfb`,
  `permissions.py` is 5/5 including two message strings, the C1 fixes).
- `django_strawberry_framework/resource_policy.py`, `django_strawberry_framework/types/resolvers.py`
  - pass 1's prose-only hunks, untouched this pass.
- `tests/utils/test_querysets.py` - the flipped seal row plus R1 / R2 / R3.
- `tests/test_resource_policy.py` - P6, and `Item` added to the existing `apps.products.models`
  import that P6 needs.
- `examples/fakeshop/test_query/test_resource_policy_api.py` - the default-manager mount, the
  prefetching probe schema and its three mounts, L1 and L2, and the module docstring's row-group
  enumeration.
- `examples/fakeshop/test_query/test_list_field_api.py`,
  `examples/fakeshop/test_query/test_list_field_async_api.py` - L3, the re-pinned refusal rows.

`examples/fakeshop/apps/library/models.py`, `test_library_api.py` and
`test_relations_async_api.py` are unedited (superseded by P2-2: `Loan` declares `objects = LoanQuerySet.as_manager()`): the mount is per-row, so no other loans path changed
shape and no re-pin was owed anywhere else in the tree (the full sweep below is what says so).

### Tests added or updated

Package tier, `tests/utils/test_querysets.py`:

- `tests/utils/test_querysets.py::test_a_subclass_result_with_a_pending_deferred_filter_seals_with_it_baked`
  - the flip of `test_unresolved_deferred_filter_subclass_result_fails_closed`, at the same seam
  (`apply_type_visibility_sync` over a subclass hook result). It now pins that a no-override
  subclass carrying a well-formed `(False, (), {"name": "later"})` SEALS, that the returned object
  is an exact `QuerySet`, and that the predicate is in the compiled SQL through
  `as_sql()` - the idiom `test_deferred_filter_never_dispatches_instance_shadowed_inplace` already
  uses. Renamed, not deleted; `grep -rn` over the tree found the old name in no citer but this
  artifact.
- `tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed`
  (R1) - parametrized `[wrong-arity]`, `[negate-not-a-bool]`, `[kwargs-not-a-dict]`,
  `[foreign-value]` over a SUBCLASS candidate, each asserting the exact `("untrusted", ...)` tuple
  and no sealed queryset. Three of the four were unreachable for a subclass before the gate
  deletion.
- `tests/utils/test_querysets.py::test_a_deferred_filter_negate_that_is_not_a_bool_fails_closed_on_an_exact_queryset`
  (R2) - the new boundary on the path that is reachable at HEAD and was unpinned there, so the
  boundary does not rest only on rows the gate removal created.
- `tests/utils/test_querysets.py::test_a_deferred_filter_negate_is_refused_without_reaching_its_own_bool`
  (R3) - a `negate` whose `__bool__` appends to a spy: the defect is returned and the spy never
  fires, which is what proves the check PRECEDES the truth test rather than accompanying it.
- Every existing exact-`QuerySet` deferred-filter row in the module is byte-identical. They are the
  controls, and their silence under both mutations below is recorded there.

Package tier, `tests/test_resource_policy.py` (the seven P/B rows of pass 1 stay as built):

- `tests/test_resource_policy.py::test_a_relation_source_from_a_project_queryset_class_keeps_its_relation_predicate`
  (P6) - the pending state is produced by calling Django's own
  `parent.items._apply_rel_filters(_ProjectQuerySet(model=Item))`, never hand-planted, so the row
  cannot drift from what Django writes. It asserts the rebuild is an exact `QuerySet`, that the
  compiled SQL carries the relation predicate and the parent's pk as a parameter, that the window
  is the relation's own leading rows, and that every returned row belongs to that parent.

Live tier, `examples/fakeshop/test_query/test_resource_policy_api.py`:

- `_project_relation_manager()` mounts `Manager.from_queryset(_ProjectLoanQuerySet)()` as `Loan`'s
  DEFAULT manager through `Loan._meta.local_managers` + `_meta._expire_cache()`, restoring both in
  `finally`. `examples/fakeshop/apps/library/models.py` stays unedited (superseded by P2-2: `Loan` declares `objects = LoanQuerySet.as_manager()`), so the control is the same
  relation, the same document and the same seed with the mount simply absent.
- `examples/fakeshop/test_query/test_resource_policy_api.py::test_a_project_queryset_class_relation_costs_what_djangos_own_manager_costs[two-parents]`
  and `[three-parents]` (L1) (renamed by P2-2 to `…costs_two_prefetch_queries`, one arm) - the same document over a prefetching mount, once with the mount and
  once without, asserting the identical payload, equal counts, and the ABSOLUTE
  `CARRY_RELATION_QUERIES = 2`.
- `examples/fakeshop/test_query/test_resource_policy_api.py::test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited`
  (L2) - the async transport, asserting rows only. The instrument warning is not waived: a
  `CaptureQueriesContext` opened on the calling thread cannot see ORM work a `sync_to_async` worker
  thread does, so an empty capture there is indistinguishable from a green zero. The payload cannot
  be produced without the relation's rows, so rows are the honest assertion and no count is claimed.
- `examples/fakeshop/test_query/test_list_field_api.py::test_holder_branches_a_malformed_apply_sync_result_names_its_own_defect[malformed-deferred-filter]`
  and its async twin
  `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_holder_branches_a_malformed_apply_async_result_names_its_own_defect[malformed-deferred-filter]`
  (L3) - re-pinned, not deleted or weakened. The override still returns a subclass; the planted
  state is now a non-`bool` `negate` (`(1, (), {"name": "A"})`), the same shape on both transports,
  and the asserted substring names it (`deferred filter negate is a int`). The surrounding table,
  the message prefix and the `resolver_queries` expectation are unchanged; only the id, the planted
  state and the substring moved. Both class docstrings carried the falsified premise ("Django
  leaves a `_deferred_filter` only on an EXACT plain queryset") and are rewritten to name what the
  class now stands for.

**The absolute live count, re-derived rather than carried.** The plan's number is 2 and this pass
measured 2 independently, at both cardinalities, on the shipped mounts - so the row asserts the
measured number and the plan's is not taken on trust. The mounted run was also proven to REACH the
seam rather than merely to pass: a probe wrapping
`django_strawberry_framework/types/resolvers.py`'s `normalized_row_source` recorded
`_ProjectLoanQuerySet` once per parent row under the mount and `QuerySet` without it.

### Validation run

Explicit paths on every write-mode command; never a bare `.`, never a shell variable holding a
path list (zsh splits it into one word and ruff then fails on a single nonexistent file, which
this pass hit and re-ran).

- `uv run ruff format <the nine files>` - pass, "9 files left unchanged" on the final run.
- `uv run ruff check --fix <the same nine>` - pass, "All checks passed!".
- `uv run python scripts/check_trailing_commas.py --check <the same nine>` - pass, exit 0 (one
  violation found and fixed on the way: R1's `ids=[...]` needed exploding at the four-element
  threshold).
- ASCII check over the nine - 0 bytes above 127 in each.
- `uv run python scripts/check_citations.py --check` - pass, 1104 citations resolve.
- `git status --short` after both ruff invocations - the nine paths above, plus, unedited by this
  pass: `docs/README.md` (Cohort B), `docs/builder/DONE/build-050-...` (Worker 0),
  `docs/spec-050-...md` and `docs/spec-050-...-rationale.md` (Worker 1), and the baseline-dirty
  concurrent set `docs/bug_hunt/*`, `docs/feedback.md`, `examples/fakeshop/db.sqlite3`. **Nothing
  outside the cohort's writable set was edited or reverted.**
- `uv run pytest -n0 tests/test_resource_policy.py tests/utils/test_querysets.py --no-cov -q` -
  **622 passed** (615 at pass 1, plus R1's four cases, R2, R3 and P6).
- `uv run pytest -n0 examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py --no-cov -q` -
  **172 passed**.
- `uv run pytest --no-cov -q` (the full parallel sweep across all four trees, owed because the
  admission widening changes a seal verdict reachable from all five policies) - **8333 passed,
  39 skipped** in 107s, exit 0.

**One failure this pass caused and fixed in-loop, which only the full sweep could see.**
The first full sweep returned `1 failed, 8332 passed`:
`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`,
naming `examples/fakeshop/test_query/test_resource_policy_api.py` for a bare
`extensions=[DjangoOptimizerExtension]` class entry - the spelling the plan's revision specifies.
That gate is a shipped repo-wide contract (spec-029 Decision 3: a non-instance entry is
re-resolved once per operation, so a bare class hands every request a structurally cold plan
cache). The fix keeps the plan's stated REASON intact and is recorded under
`### Notes for Worker 1 (spec reconciliation)` below, not buried here. No governance file was
edited: `tests/test_ci_governance.py` is in no cohort's set and is untouched.

**A second stop-and-report, not a revert.** `django_strawberry_framework/schema.py` was CLEAN in
every `git status --short` this pass took until the last one, where it is 8 insertions / 5
deletions rewriting `DjangoSchema`'s class docstring paragraph about refusing an enforcement-
extension SUBCLASS entry. This pass did not write that file, it is in no cohort's writable set (the
DONE record's partition later folds `schema.py` into Cohort B), and it has not been touched or reverted - recorded so a later pass does not read it as this cohort's
churn. Timing worth having: it was still clean when the full parallel sweep ran, so **the 8333
figure above does not cover those hunks**.

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect` | `django_strawberry_framework/utils/querysets.py` | `if policy.carry_result_cache and result_cache is not None and type(result_cache) is not list:` -> `if False:` - builder's description (unverified prose): the exact-list refusal of a carried _result_cache is removed, so a cache Django never built is carried onto the rebuild and answers the window with its own subscript | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_resource_policy.py tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 51dd1d30683cfab6... == 51dd1d30683cfab6... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/utils/querysets.py::_RAW_LIST_SOURCE_POLICY` | `django_strawberry_framework/utils/querysets.py` | `carry_result_cache=True,` -> `carry_result_cache=False,` - builder's description (unverified prose): the raw-list row source stops carrying the fetched rows forward, so a rebuilt subclass arrives unevaluated and the window re-queries (not a refusal boundary, but not only a cost: it refuses nothing) | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_resource_policy.py tests/utils/test_querysets.py` | filecmp.cmp(shallow=False) True; sha256 51dd1d30683cfab6... == 51dd1d30683cfab6... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/utils/querysets.py::_bake_deferred_filter_or_defect` | `django_strawberry_framework/utils/querysets.py` | `if type(negate) is not bool:` -> `if False:` - builder's description (unverified prose): the exact-bool refusal of the deferred filter's negate slot is removed, so an object planted there reaches `~predicate if negate else predicate` and decides through its own __bool__ whether the relation predicate is negated | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py tests/test_resource_policy.py examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py` | filecmp.cmp(shallow=False) True; sha256 51dd1d30683cfab6... == 51dd1d30683cfab6... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/utils/querysets.py::_seal_or_defect (deferred-filter admission)` | `django_strawberry_framework/utils/querysets.py` | `bake_defect = _bake_deferred_filter_or_defect(rebuilt_query, deferred, cls_name)` -> `if type(candidate) is not models.QuerySet: return None, ("untrusted", f"{cls_name} carries an unresolved deferred fil...` - builder's description (unverified prose): the deleted exact-QuerySet class gate is restored ahead of the bake, so a candidate that is not exactly models.QuerySet is refused for a pending deferred filter instead of having it baked (an admission WIDENING, not a boundary: it refuses nothing; recorded so the widening is proven distinguishing at both tiers) | **9** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py tests/test_resource_policy.py examples/fakeshop/test_query/test_resource_policy_api.py` | filecmp.cmp(shallow=False) True; sha256 51dd1d30683cfab6... == 51dd1d30683cfab6... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/utils/querysets.py::_seal_or_defect` - pinned
2. `django_strawberry_framework/utils/querysets.py::_RAW_LIST_SOURCE_POLICY` - pinned
3. `django_strawberry_framework/utils/querysets.py::_bake_deferred_filter_or_defect` - pinned
4. `django_strawberry_framework/utils/querysets.py::_seal_or_defect (deferred-filter admission)` - pinned

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/utils/querysets.py::_seal_or_defect`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 5 failed, 617 passed in 6.46s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 622 passed in 6.41s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list[list-subclass]`
   - `tests/utils/test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list[tuple]`
   - `tests/utils/test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list[foreign-object]`
   - `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_rather_than_carried`
   - `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_when_awaited`
2. `django_strawberry_framework/utils/querysets.py::_RAW_LIST_SOURCE_POLICY`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 5 failed, 617 passed in 7.46s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 622 passed in 7.01s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds`
   - `tests/test_resource_policy.py::test_a_coordinate_window_over_an_evaluated_project_queryset_class_reads_carried_rows`
   - `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_rather_than_carried`
   - `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited`
   - `tests/test_resource_policy.py::test_a_result_cache_that_is_not_a_list_is_refused_when_awaited`
3. `django_strawberry_framework/utils/querysets.py::_bake_deferred_filter_or_defect`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 5 failed, 789 passed in 18.84s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 794 passed in 19.99s =============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed[negate-not-a-bool]`
   - `tests/utils/test_querysets.py::test_a_deferred_filter_negate_that_is_not_a_bool_fails_closed_on_an_exact_queryset`
   - `tests/utils/test_querysets.py::test_a_deferred_filter_negate_is_refused_without_reaching_its_own_bool`
   - `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_holder_branches_a_malformed_apply_async_result_names_its_own_defect[malformed-deferred-filter]`
   - `examples/fakeshop/test_query/test_list_field_api.py::test_holder_branches_a_malformed_apply_sync_result_names_its_own_defect[malformed-deferred-filter]`
4. `django_strawberry_framework/utils/querysets.py::_seal_or_defect (deferred-filter admission)`
   - file mutated: `django_strawberry_framework/utils/querysets.py`
   - pytest summary: `======================== 9 failed, 756 passed in 24.18s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 765 passed in 25.17s =============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/utils/test_querysets.py::test_a_subclass_result_with_a_pending_deferred_filter_seals_with_it_baked`
   - `tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed[wrong-arity]`
   - `tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed[negate-not-a-bool]`
   - `tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed[kwargs-not-a-dict]`
   - `tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed[foreign-value]`
   - `tests/test_resource_policy.py::test_a_relation_source_from_a_project_queryset_class_keeps_its_relation_predicate`
   - `examples/fakeshop/test_query/test_resource_policy_api.py::test_a_project_queryset_class_relation_costs_what_djangos_own_manager_costs[two-parents]`
   - `examples/fakeshop/test_query/test_resource_policy_api.py::test_a_project_queryset_class_relation_costs_what_djangos_own_manager_costs[three-parents]` (renamed by P2-2 to `…costs_two_prefetch_queries`, one arm)
   - `examples/fakeshop/test_query/test_resource_policy_api.py::test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

**What the four entries are.** Entry 3 is the pass's ONE new boundary. Entries 1 and 2 are pass
1's, re-run here so the record describes the shipped bytes (entry 2 is not a refusal boundary,
but not only a cost). Entry 4 is the admission WIDENING, which refuses nothing and is therefore not a
boundary either; the plan requires it to be proven distinguishing and records the measurement
beside the boundary. Neither entry 2 nor entry 4 carries a `why 0` judgement: no entry measured
zero rows.

- **Entry 3, the `negate` boundary: 5 rows, 2 of them live, 0 collection/setup errors.** Above the
  weakly-pinned threshold, and the live pair is what makes the boundary reachable over the wire
  through both public overrides rather than only through a direct `_seal_or_defect` call.
- **Entry 4, the widening: 9 rows, 6 in the package tier and 3 in the live tier** - comfortably
  over the plan's "at least two rows per tier", and both L1 cardinalities plus L2 are among them,
  so the live rows are distinguishing and not merely green.
- **The controls stayed silent, which is the other half of entry 4's meaning.** No existing
  exact-`QuerySet` deferred-filter row failed under either mutation:
  `test_exact_queryset_pending_deferred_filter_is_resolved`,
  `test_pending_deferred_filter_over_foreign_query_never_dispatches`,
  `test_deferred_filter_never_dispatches_instance_shadowed_inplace`,
  `test_deferred_filter_never_dispatches_instance_shadowed_add_q`,
  `test_malformed_deferred_filter_fails_closed_instead_of_leaking`,
  `test_deferred_filter_slot_never_truth_tested`,
  `test_deferred_filter_wrong_arity_tuple_fails_closed`,
  `test_deferred_filter_bake_leaves_candidate_unmutated_and_is_repeatable`,
  `test_deferred_plain_model_instance_still_seals` and
  `test_related_manager_queryset_seals_and_scopes_to_its_parent` are all absent from both
  node-id lists. The gate deletion changed the subclass path and nothing on the common one.
- Under entry 3's mutation, `[wrong-arity]`, `[kwargs-not-a-dict]` and `[foreign-value]` also
  stayed silent, so the mutation isolates the `negate` slot rather than perturbing the shape
  proof generally.

### Hot-path budget

The plan declares the cohort hot-path and the revision names two numbers: the relation's query
count before and after beside the plain-manager control, and a wall-clock PROXY, because a query
count cannot see this change's actual added cost - the bake plus the post-bake
`_combined_query_table_defect` re-walk now run for a subclass relation source, once per parent row
on the many-side branch.

Both readings come from `docs/builder/temp-tests/050/row_carry/test_hotpath_admission.py`, same
instrument, same seed, same document, same optimizer spelling (a singleton behind a factory, one
per arm) on both sides:

```shell
uv run pytest -n0 docs/builder/temp-tests/050/row_carry/test_hotpath_admission.py --no-cov -q -s
```

"Before" was taken by `BUILD.md`'s fenced loop: anchor asserted to match exactly once, copy to
`<scratch>/dsf-hotpath-admission-before.orig`, the deleted class gate re-inserted ahead of the
bake, run, restore, `cmp` exit 0 and sha256
`51dd1d30683cfab68be09db50d41b52f56ee6669430f7f052cfcc7f719d3aac9` (working tree; the committed
`f7192bfb` file is `7dbd4755…`, 97/40) equal on both files.

| Metric | Before | After | Delta |
|---|---|---|---|
| `patrons { name loans { note } }` under a prefetching plan, **Django's own manager** (the control), 2 parents x 3 loans | 2 queries, rows returned | 2 queries, rows returned | 0 |
| Same document, same control, 3 parents x 3 loans | 2 queries, rows returned | 2 queries, rows returned | 0 |
| Same document, relation sourced from the model's **`Manager.from_queryset` DEFAULT manager**, 2 parents | 2 queries, **request REFUSED** (typed `ConfigurationError`, `data: null` on the field) | **2 queries, rows returned** | refusal -> parity |
| Same, 3 parents | 2 queries, **request REFUSED** | **2 queries, rows returned** | refusal -> parity |
| Wall-clock median over **50** executions, 3 parents x 3 loans, control | 0.806 ms | 0.793 ms | -0.013 ms (noise) |
| Wall-clock median over **50** executions, 3 parents x 3 loans, mounted | 1.648 ms | 1.003 ms | **-0.645 ms** |
| Mounted minus control, same run | +0.842 ms | **+0.210 ms** | **-0.632 ms** |

Read honestly, and the "before" column is not a cost comparison at the top of the table: before the
change the mounted relation did not deliver rows at all, so its two queries are the parent query
plus the optimizer's prefetch with the field erroring out. The wall-clock rows ARE comparable in
both columns, because both measure a completed operation - before, the mounted arm spent 0.842 ms
more than its control building and rendering a refusal; after, it spends 0.210 ms more than its
control (about 26%) and returns the rows. That residual +0.210 ms is the number the maintainer is
owed: it is the bake plus the post-bake genuineness re-walk, run once per parent row, that an
exact-`QuerySet` relation already pays today and a `Manager.from_queryset` relation now pays too.
Whether that trade is acceptable is the maintainer's call, not this pass's.

Pass 1's package-tier numbers stand unchanged and are not re-measured here: the raw-list seam
itself costs 0 queries for an evaluated exact `QuerySet` (control, 0 before and after) and 1 -> 0
for an evaluated project queryset class.

### Floor verification

The plan assigns this pass the two package modules; the full twenty-three-path scope (the floor at `f7192bfb`; 27 at HEAD) stays the
final gate's. Versions and recipe read from `docs/builder/BUILD.md` `## Floor verification` at run
time. The venv from pass 1 was reused after confirming its contents rather than rebuilt.

- scratch venv (outside the repo): `<scratch>/dsf-floor`.
- resolved versions, as read by `uv pip list --python <scratch>/dsf-floor/bin/python`:
  `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 25.2`, `pytest 9.1.1`,
  `django-strawberry-framework 0.0.15` (editable, this checkout); interpreter `Python 3.10.19`.
- scope as run:
  `<scratch>/dsf-floor/bin/python -m pytest tests/test_resource_policy.py tests/utils/test_querysets.py --no-cov -q -p no:cacheprovider`
  - **618 passed, 4 skipped**, pass. (The four skips are the `Schema.stream` rows the module skips
  below strawberry-graphql 0.319.0 - the floor behaving as the suite declares.)
- **The pending-`_deferred_filter` rows passed at the floor**, which the revision asks to be stated
  explicitly because `RelatedManager._apply_rel_filters` is the seam the whole change turns on and
  its body differs between the floor's Django and the shared `.venv`'s. Run as a named selection:
  `test_a_relation_source_from_a_project_queryset_class_keeps_its_relation_predicate`,
  `test_a_subclass_result_with_a_pending_deferred_filter_seals_with_it_baked`,
  `test_a_subclass_deferred_filter_state_django_never_writes_fails_closed` (4 cases),
  `test_a_deferred_filter_negate_that_is_not_a_bool_fails_closed_on_an_exact_queryset`,
  `test_a_deferred_filter_negate_is_refused_without_reaching_its_own_bool`,
  `test_exact_queryset_pending_deferred_filter_is_resolved`,
  `test_related_manager_queryset_seals_and_scopes_to_its_parent` - **10 passed**.
- shared `.venv` unmutated: `uv pip list` in the repo read `django 6.1`,
  `strawberry-graphql 0.324.0`, `django-filter 26.1` **before and after** the floor run, the same
  three readings both times. The explicit `--python` is what keeps `uv pip` out of it.

### Implementation notes

- **The gate deletion is two lines removed, not a policy axis added.** The plan assessed and
  rejected an axis; nothing in the implementation reopened that. `_SealPolicy` is untouched this
  pass apart from pass 1's `carry_result_cache`, and `_bake_deferred_filter_or_defect` gained one
  conjunct inside the block that already owns the shape proof - no second refusal message, no new
  defect code, no new arm at any message site.
- **`negate` is checked FIRST, immediately after the unpack.** It is the tuple's first element and
  the last of the three to have been unpinned; putting it ahead of `kwargs` / `args` keeps the
  block reading in slot order. Position inside the helper has no bearing on the canonical defect
  ordering, which is a property of `_seal_or_defect`'s codes, and `untrusted` keeps its fixed place.
- **R1 uses `1` for the non-`bool` `negate` rather than a truthy object**, and R3 uses the spy. Two
  rows because they answer different questions: R1 says the shape is refused, R3 says the refusal
  happens before anything consults the value's truthiness. A single spy row would have conflated
  them.
- **P6 builds its pending state through `_apply_rel_filters`.** A hand-planted
  `(False, (), {...})` would pin this package against its own idea of what Django writes; calling
  Django's own related-manager machinery is what keeps the row honest across a Django bump, and it
  is the reason the floor run above is worth stating separately.
- **The live mount swaps `_meta.local_managers`, not a manager method.** `_expire_cache()` is what
  makes `Loan._default_manager` and `Loan.objects` answer with the mounted manager; both are
  restored in `finally`. Mounting the reverse relation manager's queryset class - pass 1's finding
  and the revision's measured fact 5 - leaves an exact queryset in the prefetch cache and proves
  nothing, so it is not used.
- **`CARRY_RELATION_ROWS = 10` deliberately does not truncate.** This group's subject is what the
  relation COSTS; a ceiling clipping the payload would make every comparison agree for the wrong
  reason. The truncation contract is the neighbouring hostile-relation group's, at a bound of one.
- The measurement module `docs/builder/temp-tests/050/row_carry/test_hotpath_admission.py` and the
  updated `proofs.json` are scratch beside pass 1's `test_measure.py` / `test_hotpath.py`. Deleted
  by explicit path at closeout.

### Notes for Worker 3

- Nine files. `resource_policy.py` and `types/resolvers.py` carry ONLY pass 1's prose hunks and are
  unchanged this pass; `permissions.py` is prose-only for this pass (the committed `f7192bfb` file is 5/5 including two
  message strings) and owes the inverse proof
  shape - every changed line in it is inside a docstring, which `git diff` shows directly.
- The one executable change in `utils/querysets.py` this pass is +7 lines
  (`_bake_deferred_filter_or_defect`'s `negate` check) and -2 lines (`_seal_or_defect`'s class
  gate). Everything else in that file's diff is docstring, comment or pass 1's carry.
- `scripts/review_inspect.py` was NOT re-run. Worker 1's planning pass ran it on
  `utils/querysets.py` and recorded the overview path; this pass's net executable delta to that
  file is five lines. Recorded as a skip with the reason rather than left silent.
- If you re-run the failability subset, re-run at the scopes recorded above and compare node-id
  SETS, not numbers. Entries 3 and 4 use DIFFERENT scopes from entries 1 and 2 (they reach the live
  tree), and a narrower scope moves both counts.
- The live L2 row asserts no query count on purpose, and says so in its own docstring. The reason
  is the `sync_to_async` thread boundary, not convenience.
- `examples/fakeshop/test_query/README.md` is in no cohort's writable set and was not touched. Its
  suite map indexes modules; the module docstring it points at is the authoritative description and
  is what this pass updated, so the map is not stale - worth confirming independently.

### Notes for Worker 1 (spec reconciliation)

**1. The optimizer ENTRY SPELLING in the plan's live probe is refused by a shipped repo-wide gate,
and the spec now states the refused spelling as a requirement.** This is the one place the
implementation departs from the revision's literal text, and it is recorded here rather than in
`### Implementation notes` because it is a plan-level call.

The revision requires "the optimizer installed as a **class entry**,
`extensions=[DjangoOptimizerExtension]`", for a measured reason: the plan cache lives on the
extension INSTANCE and holds the generated `Prefetch` and hence its child queryset across
requests, so a shared instance would let the mounted row decide what the control measures.
`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`
forbids exactly that spelling across every first-party `.py`, citing spec-029 Decision 3: a bare
class is re-resolved once per operation, giving a structurally zero plan-cache hit rate. The full
sweep failed on it.

What landed keeps the reason and drops the spelling: `_carry_relation_schema` takes an `arm`
argument, is `@cache`d on `(patron_type, arm)`, and each arm builds its OWN
`DjangoOptimizerExtension()` behind `extensions=[lambda: optimizer]` - so the control and the
mounted row still have SEPARATE plan caches, which is the property the revision actually needs,
while each arm's cache is warm across its own requests, which is the property spec-029 requires.
Three mounts (`rp-carry-relation/`, `rp-carry-relation-mounted/`,
`rp-carry-relation-mounted-async/`) rather than two. This is proven, not argued: entry 4's
failability run shows BOTH L1 cardinalities and L2 failing when the class gate is restored, so the
control is still a control and the rows are still distinguishing.

**Amendment.**

- where it lives: `docs/spec-050-list_field_arguments-0_0_15.md`, `## Test plan` ->
  `### The raw-list row source`, the sentence beginning "The probe schema installs the optimizer".
- current wording, quoted: "The probe schema installs the optimizer as a class entry so each
  operation gets its own plan cache: the plan holds the generated `Prefetch` and therefore its
  child queryset across requests, and a shared instance would make the control measure the mounted
  row."
- recommended replacement: "The mounted arm and its control get SEPARATE schemas, each with its
  own optimizer singleton behind a factory: the plan holds the generated `Prefetch` and therefore
  its child queryset across requests, so one instance shared between the two arms would make the
  control measure the mounted row. The optimizer is never entered as a bare class - spec-029
  Decision 3 forbids it repo-wide, because a non-instance entry is resolved once per operation and
  a class therefore hands every request a cold plan cache."

**2. `docs/GLOSSARY.md` "Sealed execution queryset" still has no owner, and the admission change
adds nothing to what the plan already recorded.** Pass 1 falsified its `_result_cache` clause; this
pass falsifies no further glossary sentence - `grep -rn 'deferred filter\|_deferred_filter'` over
`docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `README.md` and `KANBAN.md` returns **zero**
hits, so the deferred-filter vocabulary lives only in source docstrings, the specs and the tests,
all of which this pass corrected or owns. The plan's exact replacement paragraph for the glossary
body is still the open item, still routed to the maintainer.

**3. The two archived specs the revision routed to the maintainer are still live and unedited**
(`docs/SPECS/spec-045-visibility_boundary-0_0_14.md` #"unresolved deferred filter, unsealable
prefetch child" and `docs/SPECS/spec-034-permissions-0_0_10.md` #"an unresolved deferred filter").
Amending a shipped spec is a round over that spec, not a slice edit, and neither is in any cohort's
set. Re-confirmed present at this HEAD; the one-word fix ("unresolved" -> "malformed") is unchanged.

**4. Not a finding, recorded because a later reader will hit it.** `_apply_rel_filters` sets
`_defer_next_filter` and lets `.filter(**core_filters)` store the tuple on `self._chain()`, which
preserves the candidate's class - so the pending predicate is on the SUBCLASS for a
`Manager.from_queryset` relation and on an exact `QuerySet` otherwise, and the two differ in
nothing else. That is why the fix is a deletion rather than a new admission rule, and why P6
builds its state through Django instead of planting it.

---

## Review (Worker 3)

### Failability re-run: mutations recorded BEFORE they are made

Two boundaries re-run independently, both inside the mandatory floor's spirit (the pass's one new
boundary, plus the admission widening whose distinguishing measurement the plan required). Run by
`uv run python scripts/prove_failability.py docs/builder/temp-tests/050/row_carry/proofs-w3.json
--scratch-root <scratch>/proofs-w3`, which performs the `BUILD.md` fenced loop in order (anchor
asserted to match exactly once BEFORE the pre-mutation copy, pre-mutation run, mutate, run,
restore, byte-compare). Manifest written by Worker 3, entries transcribed from the build report's
recorded mutations and scopes so the node-id sets are comparable:

- `django_strawberry_framework/utils/querysets.py::_bake_deferred_filter_or_defect` -- anchor
  `    if type(negate) is not bool:` replaced by `    if False:`; scope
  `tests/utils/test_querysets.py tests/test_resource_policy.py
  examples/fakeshop/test_query/test_list_field_api.py
  examples/fakeshop/test_query/test_list_field_async_api.py`.
- `django_strawberry_framework/utils/querysets.py::_seal_or_defect (deferred-filter admission)` --
  anchor `        bake_defect = _bake_deferred_filter_or_defect(rebuilt_query, deferred, cls_name)`
  with the deleted exact-`QuerySet` class gate re-inserted ahead of it; scope
  `tests/utils/test_querysets.py tests/test_resource_policy.py
  examples/fakeshop/test_query/test_resource_policy_api.py`.

Results and node-id set comparison are recorded below once the run completes. Nothing is left
mutated; the restore is proved by byte comparison inside the tool's own `finally`.

### Failability audit

**Records audited: all four entries.** Each carries the boundary by symbol-qualified path, the
exact mutation, the listed node ids, the focused scope as run, a green pre-mutation state of that
same scope (`622 passed` / `794 passed` / `765 passed`, pytest exit 0), **0** collection/setup
errors, and a byte-compared restore (`filecmp.cmp(shallow=False)` plus sha256). No entry measured
zero rows, so no `why 0` judgement is owed and none is missing. Counts: 5 / 5 / 5 / 9 - none
weakly pinned. Entries 2 and 4 are correctly labelled as NOT boundaries (a carry mutation that is not only
a cost, and an admission widening); recording them beside the boundary is what the plan asked for and both are
distinguishing.

**Re-run independently: entries 3 and 4** - the pass's one new boundary
(`_bake_deferred_filter_or_defect`'s exact-`bool` `negate` refusal) and the admission widening
(`_seal_or_defect`'s deleted class gate). **Accepted on Worker 2's record: entries 1 and 2**, pass
1's carry entries, already re-run by Worker 2 against the shipped bytes and outside this pass's
new code.

**Node-id SET comparison, at Worker 2's recorded scopes (not counts):**

| Entry | Worker 2 | Worker 3 re-run | Set difference |
|---|---|---|---|
| 3, `negate` boundary | 5 rows | 5 rows, `5 failed, 789 passed`, exit 1, pre-mutation `794 passed` exit 0, 0 errors | **empty - identical sets** |
| 4, admission widening | 9 rows | 9 rows, `9 failed, 756 passed`, exit 1, pre-mutation `765 passed` exit 0, 0 errors | **empty - identical sets** |

Entry 3's set, re-derived:
`tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed[negate-not-a-bool]`,
`::test_a_deferred_filter_negate_that_is_not_a_bool_fails_closed_on_an_exact_queryset`,
`::test_a_deferred_filter_negate_is_refused_without_reaching_its_own_bool`,
`examples/fakeshop/test_query/test_list_field_async_api.py::test_async_holder_branches_a_malformed_apply_async_result_names_its_own_defect[malformed-deferred-filter]`,
`examples/fakeshop/test_query/test_list_field_api.py::test_holder_branches_a_malformed_apply_sync_result_names_its_own_defect[malformed-deferred-filter]`.

Entry 4's set, re-derived: the flipped seal row, all four `R1` cases, `P6`
(`tests/test_resource_policy.py::test_a_relation_source_from_a_project_queryset_class_keeps_its_relation_predicate`),
both `L1` cardinalities and `L2`. Six package rows and three live rows, so the widening is
distinguishing at both tiers and the live rows are not merely green.

**Restore verified independently of the tool's own claim:** after my run,
`shasum -a 256 django_strawberry_framework/utils/querysets.py` =
`51dd1d30683cfab68be09db50d41b52f56ee6669430f7f052cfcc7f719d3aac9` (working tree; the committed
`f7192bfb` file is `7dbd4755…`, 97/40), byte-identical to the hash the
build report records for the shipped file; `grep -c 'if type(negate) is not bool:'` = 1,
`grep -c 'carries an unresolved deferred filter'` = 0, `grep -c 'if False:'` = 0, no
`ACTIVE-MUTATION.json`, and `git diff HEAD --stat` still reads `92 insertions, 35 deletions` (committed: 97/40).
Nothing is left mutated.

### High:

None.

### Medium:

#### Decision 8 says the visibility seals REFUSE an evaluated source; the code admits it and drops the cache

`docs/spec-050-list_field_arguments-0_0_15.md` #"Every other seal keeps its `require_unevaluated`
verdict: a visibility hook's input and result" states that a visibility hook's input and result
"are still refused when evaluated". They are not: `require_unevaluated` defaults to `False` and
only `_RAW_LIST_SOURCE_POLICY`'s sibling `_ORDERSET_RESULT_POLICY` (at `f7192bfb`; now `_SIDECAR_RESULT_POLICY`, which also seals `FilterSet.apply_*` returns) sets it
(`django_strawberry_framework/utils/querysets.py:2816`). An evaluated source at the visibility
boundary is SEALED with its cache dropped, which is a different verdict with a different security
argument, and the shipped code says so precisely - `_SealPolicy`'s own docstring reads "It is off
for every ``get_queryset`` seal, this surface's included". Measured, not read:
`tests/utils/test_querysets.py:406-412` seals an evaluated source in zero queries and asserts
`result._result_cache is None`, and `:1543` pins a hook's INJECTED cache being dropped rather than
refused.

Why it matters here rather than generally: this is the paragraph that draws the line the whole
cohort turns on ("That carry belongs to the raw-list seam alone"), so a reader checking the new
axis against the spec is handed a false statement of what every other policy does, and the
obvious "fix" it invites - setting `require_unevaluated=True` on the read-surface policies - would
break `spec-045`'s own contract. The sentence is pre-existing at HEAD
(`git show HEAD:docs/spec-050-list_field_arguments-0_0_15.md` line 1266), the spec is in no
cohort's writable set, and the build implements the correct behavior, so this is **escalated to
Worker 1** under `worker-3.md` "Review job" step 7 rather than held at `revision-needed`.
Recommended replacement for the clause: "Every other seal keeps its own verdict: an evaluated
source at a `get_queryset` seal is rebuilt with its `_result_cache` dropped rather than carried,
and an `OrderSet.apply_*` result is refused outright when evaluated, because ...". No test change
is owed; the rows above already pin both verdicts.

### Low:

#### `bounded_rows`'s own docstring still promises a SQL `LIMIT` for a shape that now takes a list slice

`django_strawberry_framework/resource_policy.py:1068-1072` (public surface): "A ``QuerySet``
subclass is the one shape that is rebuilt rather than reclassified: it is sealed into a plain
framework-owned queryset and sliced there, so it keeps the SQL ``LIMIT`` a counted truncation
would lose". After the carry that holds only for a subclass that arrives UNEVALUATED; one that
arrives evaluated is windowed from the carried cache, and `QuerySet.__getitem__` answers a
populated cache with `self._result_cache[k]`, so the result is a plain list and there is no
`LIMIT`. `_windowed_rows` carries the same unqualified sentence at
`django_strawberry_framework/resource_policy.py:1002-1005`, though there the new paragraph
immediately below scopes it. The build report names this drift for P2's return type but does not
carry it into the two docstrings that state it as a contract. Recommended: one clause on the
`bounded_rows` sentence ("- an unevaluated one; one that arrives evaluated is windowed from the
rows it carries"). No behavior change, no test expectation.

#### The artifact's `### Spec slice checklist (verbatim)` contradicts itself and is no longer verbatim

Two separate defects in one block, both of which Worker 1 audits ticks against:

- Both boxes read `- [x]`, while the paragraph immediately beneath them still reads "Worker 2,
  build pass: neither box is ticked ... The LIVE half of each ... did not [land]". That paragraph
  was true at pass 1 and is false now; a reader reconciling the two cannot tell which is the tick's
  warrant.
- The quoted rows are no longer the spec's. The plan revision amended `## Slice checklist` Slice 3
  and the matching `## Definition of done` row (the artifact's own `### Spec changes made` records
  both), so the spec now demands the **absolute** count, the bake, and the exact-shape refusal,
  while the "verbatim" copy still says "at Django's own manager's count" and names none of them.
  The diff satisfies the CURRENT rows - I walked each clause against it (see `### What looks
  solid`) - so this is hygiene, not a missing deliverable.

#### A count whose subject is wrong: "all five shipped `_SealPolicy` values"

`docs/spec-050-list_field_arguments-0_0_15-rationale.md:322` reports that "all five shipped
`_SealPolicy` values refused the subclass relation queryset". Seven `_SealPolicy` values are
constructed at module level (`django_strawberry_framework/utils/querysets.py:2794, 2800, 2805,
2808, 2814, 2816, 2826`); the probe covered five, omitting `_CASCADE_SEAL_POLICY` and
`_UNRECOMPOSED_CHILD_POLICY`. The conclusion is untouched - the deleted gate was class-based and
policy-independent, so all seven behaved identically - but the sentence states a population it did
not measure. Recommended: "every `_SealPolicy` the probe exercised (five of the seven constructed
at module level)", or extend the probe. Worker 1's file; recorded here rather than edited.

#### Robustness row, graded under `AGENTS.md` rule 35: the exact-queryset twin of the new cache refusal is unguarded

Measured with `docs/builder/temp-tests/050/row_carry/test_w3_exact_cache.py`: an EXACT
`models.QuerySet` whose `_result_cache` holds an object that is not a list returns **25 rows under
a `max_list_rows` of 2** through `bounded_rows`. The new refusal
(`django_strawberry_framework/utils/querysets.py:3318`) lives inside `_seal_or_defect`, which an
exact queryset never reaches: `normalized_row_source` returns it unchanged, `_bounds_by_its_own_slice`
answers True on the container's exact type, and `QuerySet.__getitem__` then delegates the slice to
`self._result_cache[k]` - the bounded party's own subscript, which is the exact answer this seam
exists to refuse.

**This is not a defect against this card and is not a reason to hold the cohort.** Rule 35 asks for
a contract row, a feasible project shape under supported public API, and the input that reaches it.
The contract row exists (`## Definition of done` #"No raw-list row source decides its own ceiling"),
but no wire or configuration input reaches it and no supported public API writes a non-list into
Django's private `_result_cache`; only trusted application Python can, and `GOAL.md`
`## Trust boundary` puts that inside the trusted party. It is also **pre-existing at HEAD** - the
code path is byte-identical there, the diff changes only `normalized_row_source`'s docstring - so
it is neither introduced nor worsened by this pass. Recorded because the pass just proved by
mutation that the same answer matters one branch over, and because whether the package guards a
private slot a trusted caller wrote is a contract-level question. Routed to the maintainer through
`### Notes for Worker 1 (spec reconciliation)`.

### DRY findings

**No new duplication, and one deletion.** Assessed rather than assumed:

- The `carry_result_cache` axis is the right shape and the alternative was correctly rejected. One
  field on `_SealPolicy`, one check, one assignment, all inside the single function that already
  owns what a faithful rebuild carries forward, reading the SAME `state` dict the other five
  retained slots come from - so validated state and executed state provably cannot diverge, which
  is `_seal_or_defect`'s own documented property. Writing `sealed._result_cache` inside
  `normalized_row_source` would have re-read the instance state a second time and split that
  ownership across two functions.
- **Existence challenge on the axis, answered by measurement rather than waived:** it cannot be
  deleted and "always carry" inlined. `tests/utils/test_querysets.py:1543` and `:1889` pin a
  visibility hook's injected `_result_cache` being dropped, on both colors; an unconditional carry
  would serve a synthetic unsaved row with zero SQL. The axis has to exist and has to be per-policy.
- **The gate deletion REMOVES a divergence rather than adding one.** Before it, the exact and
  subclass paths differed on deferred-filter handling at `_seal_or_defect` while
  `_bake_deferred_filter_or_defect` proved the same shapes for both; now there is one bake path for
  every candidate and the class decides nothing. No bake logic is duplicated between the two paths -
  there is only one path.
- The `negate` check is one conjunct inside the block that already owns the shape proof, reusing
  the established `f"{cls_name} deferred filter ... is a {_safe_type_name(...)}"` message shape,
  the `untrusted` code, and no new arm at any message site. `_raw_list_source_message`'s generic
  `untrusted` arm renders the new `_result_cache` detail correctly (asserted at the package tier by
  `test_a_result_cache_that_is_not_a_list_is_refused_rather_than_carried`).
- **Repeated literals, from the helper's own output** (below): `untrusted` at **73x** in this
  module with no named constant, up exactly one from the 72 the plan recorded (pass 1 added the
  `_result_cache` return, pass 2 added the `negate` return and deleted the class gate's). That is
  the module's established convention, not a regression this pass introduces, and the codes are the
  keys `_defect_message`'s arm maps read - extracting them is a package-wide call, not a slice's.
  No other repeated literal in the helper's list is touched by this diff.

**Escalated existence challenge, out of diff:** `_UNRECOMPOSED_CHILD_POLICY`
(`django_strawberry_framework/utils/querysets.py:2805`) has **zero** production readers since
commit `fd39cac6` swapped `optimizer/walker.py::_build_child_queryset` onto
`_PREFETCH_CHILD_POLICY`; its only remaining reader is `tests/utils/test_querysets.py:5035`, and
`_SealPolicy`'s `reject_sliced` bullet still names "the optimizer walker's nested-connection
child" as a live surface it is off for. That is a concurrent session's committed change, in no
cohort's writable set, so it is routed rather than acted on.

### Static inspection helper

Run as required (`BUILD.md` `### When to run the helper during build`: the slice touches an
existing `.py` under `utils/`, and adds 30+ lines to a package file). No skips.

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/utils/querysets.py \
  --output-dir <scratch>/inspect
```

Shadow files at `<scratch>/inspect/django_strawberry_framework__utils__querysets.overview.md` and
`.stripped.py`; shadow line numbers are not cited anywhere above.

**Marker walk.** 51 executable marker lines, 99 calls of interest, 31 control-flow hotspots, 0
TODOs. The Django/ORM markers the diff owns were walked individually: the `QuerySet` markers at
the seal's state reads (`state.get("_iterable_class")`, `state.get("_hints")`,
`state.get("_fields")`) are the slots the new `state.get("_result_cache")` joins, all from one
`object.__getattribute__` extraction; the `prefetch_related` markers confirm the carried assignment
sits after `_sealed_prefetch_related_lookups`, so a child that cannot be sealed still fails the
outer seal before any row travels. `getattr()` 31x / `isinstance()` 19x / `issubclass()` 14x were
checked against the fail-open list: **the diff adds none of them** - every new read is
`state.get(...)` on the exact instance dict, every new test is `type(x) is <builtin>`, and there is
no clamp, no `or` fallback, no bare `except`, and no truthiness test on a value that can be absent
(`result_cache is not None` and `deferred is not None`, never `if result_cache:`).

### Fail-open shape hunt

Hunted where the diff computes an input to a limit or a rejection. Clean, and one result is
load-bearing enough to state as a measurement rather than a reading: under the `negate` mutation,
the `[wrong-arity]`, `[kwargs-not-a-dict]` and `[foreign-value]` rows stayed silent, so the new
check isolates its slot instead of perturbing the shape proof generally. Two ordering properties
that would each have been a High if wrong, both verified in source:

- **No truth test precedes the exact-`bool` check.** `if type(negate) is not bool:` is the first
  statement after `negate, args, kwargs = deferred`, and the unpack itself is reached only through
  `type(deferred) is not tuple or len(deferred) != 3`, whose short-circuit puts the type proof
  before `len()`. The only consumer-dispatch point downstream - `~predicate if negate else
  predicate` - is 29 lines further on. `R3`
  (`test_a_deferred_filter_negate_is_refused_without_reaching_its_own_bool`) pins it with a
  `__bool__` spy that must never fire, and my re-run of entry 3 shows that row failing when the
  check is removed, so the ordering is pinned and not merely present.
- **No consumer dispatch on anything unproven.** `PROHIBITED_FILTER_KWARGS.intersection(kwargs)`
  runs after `type(kwargs) is not dict`; `for value in args` after `type(args) not in (tuple,
  list)`; `models.Q(*args, **kwargs)` after both plus the exact-`str` key proof.
- **The carried cache is proven before it is carried, and the check reads the SAME local the
  assignment uses** (`result_cache`, read once at
  `django_strawberry_framework/utils/querysets.py:3317`), so validated state and carried state
  cannot diverge. `type(result_cache) is not list` rather than `isinstance` is correct for the
  stated reason and is pinned by the `[list-subclass]` parametrization, whose absence the `[tuple]`
  case would not have distinguished.
- **`_prefetch_done` is deliberately not carried, and I confirmed the claim that nothing iterates
  the carried rebuild.** `_bounds_by_its_own_slice` is True for the exact rebuilt queryset, so both
  colors reach `result[start:stop]`; `_windowed_rows_async` hands a queryset straight back to
  `_windowed_rows` because `is_async_only_iterable` is False for a queryset. Django's
  `__getitem__` answers a populated cache before `_fetch_all`, so `_prefetch_related_objects`
  cannot run off a carried cache. Had anything iterated it, the missing `_prefetch_done` would have
  re-run every prefetch - unmeasurable by the identity assertions the async rows use.

### Query-shape and live-mount verification

Verified mechanically, not read (`BUILD.md` `### Query-shape tests must pin the load-bearing
property`). Temp module `docs/builder/temp-tests/050/row_carry/test_w3_mount.py`, 3 passed:

- **The mount reaches the seam, and the control does not.** A spy on
  `django_strawberry_framework/types/resolvers.py`'s own `normalized_row_source` binding records
  `{"_ProjectLoanQuerySet"}` under the mount and `{"QuerySet"}` without it, over the same document
  and the same mounts L1 uses, **exactly twice - once per parent row**, which is the prefetched
  many-side branch the carry lives on. This is the independent confirmation that L1 is not a green
  row measuring the unmounted path. Entry 4's re-run corroborates it from the other direction:
  restoring the class gate fails both L1 cardinalities and L2, which is only possible if a subclass
  candidate reaches `_seal_or_defect`.
- **The mount's restore is proven, not asserted.** After the context manager exits,
  `Loan._meta.local_managers` equals the list captured before it, `Loan._default_manager` and
  `Loan.objects` are their original types, and `Loan.objects.all()` is an exact `QuerySet` again.
  (`Loan.objects` answers with the mounted manager INSIDE the block because
  `ManagerDescriptor.__get__` resolves through `_meta.managers_map` by name, which is what
  `mounted.name = "objects"` is for - so the restore assertion is meaningful rather than vacuous.)
- **The request shape cannot route to a fallback.** `_HOSTILE_RELATION_QUERY` is
  `"{ patrons { name loans { note } } }"` - no `filter:` / `orderBy:` sidecar, no arguments at all,
  so there is nothing that could silently disable the prefetch plan. The absolute **2** at both
  cardinalities is one parent query plus one prefetch, and the payload equality is what stops a
  cheaper count meaning fewer rows.
- **The two arms genuinely hold separate plan caches.** Each arm's schema resolves a DISTINCT
  `DjangoOptimizerExtension` instance (three identities across `control` / `mounted` /
  `mounted-async`), while `@cache` returns the same schema object for a repeated arm, so each arm's
  cache stays warm across its own requests. That is exactly the property the plan wanted from a
  class entry, preserved by the singleton-behind-a-factory spelling.
- **The governance gate's reason holds.** `tests/test_ci_governance.py` - 91 passed. Its docstring
  prescribes the landed spelling verbatim ("The fix is a factory over a singleton scoped to that
  construction site: `ext = DjangoOptimizerExtension(...)` then `extensions=[lambda: ext]`"), so
  the implementation satisfies spec-029 Decision 3 and the revision's measured requirement at the
  same time. The spec's `### The raw-list row source` still asks for the forbidden class entry;
  Worker 2's amendment is correct and is seconded below.
- **L2's honesty, judged rather than accepted.** The async row asserts rows and no count, for the
  stated `sync_to_async` reason. It is still distinguishing: entry 4's node-id set contains it, so
  it fails when the admission is removed. It was judged here NOT to fail if only the carry were removed; that is wrong:
  measured at `ae52bdec`: without the carry, L2 fails with `data` None because graphql-core
  iterates the lazily sliced rebuild on the event loop and Django raises `SynchronousOnlyOperation`,
  and both L1 cardinalities fail with `assert 4 == 2`. Entry 2's scope excluded it.

### Hot-path budget

**The number exists and reproduces as recorded.** Re-run of the recorded command:

```shell
uv run pytest -n0 docs/builder/temp-tests/050/row_carry/test_hotpath_admission.py --no-cov -q -s
```

| Reading | Build report | Worker 3 re-run |
|---|---|---|
| Control, 2 parents | 2 queries, rows | `plain_manager=2`, rows `[3, 3]` |
| Control, 3 parents | 2 queries, rows | `plain_manager=2`, rows `[3, 3, 3]` |
| Mounted, 2 and 3 parents, after | 2 queries, rows | `from_queryset=2`, rows `[3, 3]` / `[3, 3, 3]`, `errors=None` |
| Wall-clock median, 50 iterations, mounted minus control | +0.210 ms | **+0.210 ms** (0.802 -> 1.011) |

Whether +0.210 ms per request (about 26%) for a `Manager.from_queryset` relation is an acceptable
price for the refusal becoming parity is the maintainer's call, not mine; my obligation is that the
number exists, sits beside the change, is the same metric on both sides, and reproduces. It does.
The "before" column is correctly recorded as a refusal rather than laundered into a cost.

### Floor verification

Recorded with the venv path outside the repo, the resolved versions as READ
(`django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 25.2`, `pytest 9.1.1`, interpreter
`3.10.19`), the scope as run, and the result (`618 passed, 4 skipped`). The pending-`_deferred_filter`
rows are separately named and passed at the floor, which the revision required because
`_apply_rel_filters` is the seam the change turns on and its body differs between the floor's Django
and the shared `.venv`'s. The shared `.venv` is recorded unmutated before and after. Not re-run
here; the record carries every field `BUILD.md` requires and the floor scope is the build pass's,
not the review's.

### Test staleness sweep, run independently of the diff's file list

Not derived from `### Files touched` - the tree a slice misses is by definition the one absent from
its diff.

- `grep -rn "unresolved deferred filter"` over every tracked `.py` and `.md`: **zero** hits in the
  package and in all four test trees by a per-line grep, which missed four wrapped sites (the
  `querysets.py:54` module docstring, the `_visibility_result_error` message, two `permissions.py`
  message strings); all were fixed in `f7192bfb`. The surviving hits are the two archived specs already routed
  to the maintainer, this artifact, and the rationale's historical measurement (correct in past
  tense at `:322`).
- `grep -rln "_deferred_filter"` over `tests/` and `examples/`: exactly the four modules in the
  diff. No fifth tree carries the vocabulary.
- `grep -rn "_result_cache"` over `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`,
  `README.md`, `KANBAN.md`, `TODAY.md`: the falsified glossary sentence (already routed, with an
  exact replacement paragraph) and three historical KANBAN rows (four lines) about the optimizer's own
  evaluated-queryset guard, which the carry does not touch. `docs/README.md:390` delegates to the
  glossary entry and states no `_result_cache` claim of its own, so Cohort B's file is not
  falsified by this cohort.
- `grep -rn "extra query"` over the package: two hits, one unrelated; the relevant one is `_SealPolicy`'s
  `require_unevaluated` bullet,
  where it is correctly scoped to the seals that discard the cache. No stale "one extra query"
  claim survives at the raw-list seam.
- Provenance sweep over every ADDED line in `django_strawberry_framework/`: zero hits for
  `previously`, `no longer`, `pass 1`, `formerly`, `used to`. Every new comment states the invariant.
- Live-tier README: `examples/fakeshop/test_query/README.md` is clean at HEAD and its suite-map row
  for this module is an INDEX; the module docstring is the authoritative description and is what the
  pass updated, so the map is not stale. Confirmed independently, as Worker 2 asked.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` prints nothing. `__all__` and the
re-export list are unchanged; the carry axis, the `negate` refusal and the admission widening are
all private. Consistent with the Definition of done's "no new public exports".

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The only prose the diff
ships is source docstrings, source comments and test docstrings, all covered above. The two doc
surfaces this cohort falsifies - the glossary entry and the two archived specs - are correctly
routed rather than edited, and I re-confirmed all three are still live and unedited at this HEAD.)

### What looks solid

- **The root-cause fix was taken over the cheap one.** The revision chose deleting the class gate
  over a `_SealPolicy` axis, and the measurement behind it (measured fact 3: the same project shape
  is refused at the visibility boundary too) is what makes an axis a knowingly partial fix. The
  shipped code matches: `_SealPolicy` is untouched this pass, and the admission is one deletion
  plus one conjunct inside the helper that already owned the shape proof.
- **The re-pins restore the rows' original intent against the new contract, and none is weakened.**
  `test_unresolved_deferred_filter_subclass_result_fails_closed` was flipped at the SAME seam and
  now asserts more than it did - the seal returns an exact `QuerySet` AND the predicate is in the
  compiled SQL - rather than being deleted. The two live `L3` rows keep their table, their message
  prefix and their `resolver_queries: 0` expectation; only the planted state and the asserted
  substring moved, and both transports plant the same shape. `permissions.py` is a one-clause
  docstring correction whose executable tokens are untouched.
- **Every clause of the spec's CURRENT Slice 3 row and DoD row is in the diff.** Window from held
  rows, exact and rebuilt subclass alike (P1-P5); count pinned at an absolute zero in the package
  tier (`django_assert_num_queries(0)`, never an equality); the `Manager.from_queryset` relation at
  Django's own manager's absolute count, two cardinalities, live (L1); the pending predicate baked
  by the same unbound `Query.add_q` (P6 through Django's own `_apply_rel_filters`; the flipped seal row
  hand-plants `(False, (), {"name": "later"})`); a state Django never writes refused
  with the typed error at BOTH tiers (R1/R2/R3 and L3).
- **P6 builds its pending state through `_apply_rel_filters`; the flipped row hand-plants it.** A hand-planted
  tuple would pin the package against its own idea of what Django writes; this is what makes the
  floor run's named selection meaningful.
- **The async rows' substitution of identity for a count is the stronger assertion,** not a
  concession: a second fetch cannot return the objects the source is already holding, and the rows
  say so in their own docstrings. P5's move to identity is better still - the build report records
  that the first proof run measured it non-distinguishing at 4 rows and that the corrected row took
  it to 5, which is the failability loop doing its job inside the build pass.
- **Concurrent-work discipline.** Two files that went dirty mid-pass (`optimizer/walker.py`, then
  `schema.py`) were recorded and left alone, with the sweep's coverage honestly qualified in both
  cases. I verified the second: `schema.py`'s hunk is docstring-only (AST identical with docstrings
  stripped), so the 8333-passed sweep still covers the executable tree.

### Temp test verification

Three modules under `docs/builder/temp-tests/050/row_carry/`, all Worker 3's, all scratch:

- `test_w3_mount.py` - 3 passed. Proves the mount reaches the seam with the project class (and the
  control does not), that the mount restores `Loan` exactly, and that the three arms hold distinct
  optimizer instances. **Disposition: not promoted.** Each property is already pinned indirectly by
  a permanent row (entry 4's failability set covers reach; the full sweep covers restore), and these
  read the suite's private helpers, which a permanent row should not.
- `test_w3_exact_cache.py` - fails by design; it is the measurement behind the Low robustness row
  above. **Disposition: not promoted, routed to the maintainer.** Promoting it would pin a contract
  the package has not decided to offer, and whether it should is contract-level, not a builder's.
- `proofs-w3.json` - my two-entry failability manifest, entries transcribed from the build report.

Deleted all four by explicit path at closeout, beside Worker 2's `test_measure.py`,
`test_hotpath.py`, `test_hotpath_admission.py` and `proofs.json`. Nothing under
`docs/builder/temp-tests/` is left executing against the tree.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium): Decision 8's `require_unevaluated` sentence is false against the code.**
  Full evidence and a recommended replacement clause are in `### Medium:` above. The spec is in no
  cohort's writable set and the sentence predates this cycle's spec edits; the resolution is a
  custodian edit, not a builder's.
- **Seconded: the optimizer entry-spelling amendment Worker 2 proposed is correct and is now proven,
  not argued.** `## Test plan` -> `### The raw-list row source` still requires the bare class entry
  that `tests/test_ci_governance.py` forbids repo-wide. The landed spelling preserves the property
  the spec actually needs - I measured three distinct optimizer instances across the three arms -
  while satisfying spec-029 Decision 3. Worker 2's recommended replacement wording is accurate;
  adopt it.
- **The DoD row's "on both transports" reads as if the ABSOLUTE count is owed on the async
  transport**, which the same spec's test plan explicitly does not ask for ("The async transport row
  asserts the same rows rather than a count"). Both readings are defensible and the implementation
  matches the test plan. Consider tightening the DoD row to "... at two parent cardinalities, and
  the same rows on both transports", so the two homes cannot be read as disagreeing.
- **Artifact hygiene before the tick audit:** the `### Spec slice checklist (verbatim)` block
  contradicts itself and is no longer verbatim (see `### Low:`). Worth resolving before auditing the
  ticks against it, since the text a tick is audited against is currently the pre-revision one.
- **Escalated existence challenge, out of diff:** `_UNRECOMPOSED_CHILD_POLICY` has had no production
  reader since commit `fd39cac6` (details in `### DRY findings`). Resolution paths: (a) delete the
  policy and its one test row, and drop the nested-connection-child clause from `_SealPolicy`'s
  `reject_sliced` bullet; (b) keep it and correct that bullet to say the walker now seals its
  prefetch child under `_PREFETCH_CHILD_POLICY`. Either is a decision about a file in no cohort's
  set, so it is the maintainer's, not mine and not Worker 2's.
- **Routed to the maintainer (robustness row, `AGENTS.md` rule 35):** an exact `QuerySet` carrying a
  foreign `_result_cache` escapes the raw-list ceiling (measured: 25 rows under a bound of 2),
  pre-existing at HEAD and unreachable from the wire. The question it raises - whether the package
  proves the shape of a private slot a TRUSTED caller wrote, when it already proves it one branch
  over - is contract-level. If the answer is yes, the fix is small and belongs in
  `normalized_row_source` rather than in the sealer, since the sealer is what an exact queryset
  never reaches.
- **Still unowned, unchanged from Worker 2's note:** the `docs/GLOSSARY.md` "Sealed execution
  queryset" body (the plan's exact replacement paragraph is still a paste, and I re-confirmed the
  falsified sentence is live at `docs/GLOSSARY.md:1891`) and the two archived specs' "unresolved" ->
  "malformed" one-word fix. All three re-confirmed present and unedited at this HEAD.

### Review outcome

`review-accepted`, with one Medium transparently escalated to Worker 1 (`worker-3.md` "Review job"
step 7): its resolution is a spec edit in a file no cohort may write, the behavior it misdescribes
is pre-existing at HEAD and correct in the code, and no change to Worker 2's diff would close it.
Every Low is either hygiene in the artifact, a one-clause docstring scoping, or a row routed with
its rejection reason recorded. No High findings. The failability records are complete and valid, my
independent re-run of the two new entries reproduced Worker 2's node-id sets exactly, the hot-path
number exists and reproduces, and nothing is left mutated.


---

## Final verification (Worker 1)

- **Spec slice checklist:** both boxes `- [x]`, re-quoted from the current spec and audited clause
  by clause in `### Spec slice checklist (verbatim)` above. Nothing is deferred and nothing is
  over-ticked.
- **DRY check across this slice and prior accepted slices:** no new duplication. The carry is one
  field on `_SealPolicy`, one validation and one assignment, all inside the single function that
  already owns what a faithful rebuild carries forward, reading the same `result_cache` local at
  both sites (`django_strawberry_framework/utils/querysets.py:3317`, `:3318`, `:3371`) so the
  validated state and the carried state cannot diverge. The admission change DELETES a divergence:
  one bake path now serves every candidate where the exact and subclass paths differed before, and
  the `negate` check is one conjunct inside the block that already owns the shape proof, reusing
  the `untrusted` code and the established message shape with no new arm at any message site. I
  ran the existence challenge on the axis myself rather than reading Worker 3's: it cannot be
  deleted in favour of an unconditional carry, because the visibility seal's injected-cache rows
  (`tests/utils/test_querysets.py::test_identity_hook_result_is_resealed_dropping_injected_cache_sync`
  and its async twin) would then serve a synthetic unsaved row with zero SQL.
- **Existing tests run:** `uv run pytest -n0 tests/test_resource_policy.py
  tests/utils/test_querysets.py --no-cov -q` - **622 passed**, exit 0.
  `uv run pytest -n0 examples/fakeshop/test_query/test_resource_policy_api.py
  examples/fakeshop/test_query/test_list_field_api.py
  examples/fakeshop/test_query/test_list_field_async_api.py --no-cov -q` - **315 passed**, exit 0.
  No `--cov*` flag in either.
- **Failability, independently re-run at the recorded scopes.** `uv run python
  scripts/prove_failability.py docs/builder/temp-tests/050/row_carry/proofs.json --scratch-root
  <scratch>/proofs --only 3 --only 4`, exit **0**. Node-id SETS, not counts:

  | Entry | Worker 2 | Worker 3 | Worker 1 re-run | Set difference |
  |---|---|---|---|---|
  | 3, the `negate` boundary | 5 rows | 5 rows | 5 rows, `5 failed, 789 passed`, exit 1, pre-mutation `794 passed` exit 0, 0 collection/setup errors | **empty - identical** |
  | 4, the admission widening | 9 rows | 9 rows | 9 rows, `9 failed, 756 passed`, exit 1, pre-mutation `765 passed` exit 0, 0 collection/setup errors | **empty - identical** |

  Entry 3's set: `tests/utils/test_querysets.py::test_a_subclass_deferred_filter_state_django_never_writes_fails_closed[negate-not-a-bool]`,
  `::test_a_deferred_filter_negate_that_is_not_a_bool_fails_closed_on_an_exact_queryset`,
  `::test_a_deferred_filter_negate_is_refused_without_reaching_its_own_bool`, and the two live
  `[malformed-deferred-filter]` rows in `test_list_field_api.py` / `test_list_field_async_api.py`.
  Entry 4's set: the flipped seal row, all four `R1` cases, `P6`, both `L1` cardinalities and `L2`
  - six package rows and three live rows. Neither entry is weakly pinned, neither measured zero
  rows, so no `why 0` judgement is owed. Nothing is left mutated: after my run
  `shasum -a 256 django_strawberry_framework/utils/querysets.py` =
  `51dd1d30683cfab68be09db50d41b52f56ee6669430f7f052cfcc7f719d3aac9` (working tree; the committed
`f7192bfb` file is `7dbd4755…`, 97/40), the hash the build report
  records for the shipped file; `grep -c 'if type(negate) is not bool:'` = 1,
  `grep -c 'carries an unresolved deferred filter'` = 0, `grep -c 'if False:'` = 0, and no
  `ACTIVE-MUTATION.json` exists under the scratch root.
- **Fail-open check, read from the diff rather than from a green suite.** The diff adds no
  `getattr`, no `isinstance`, no `or` fallback, no bare `except`, and no truthiness test on a
  value that can be absent: the two new guards are `result_cache is not None and
  type(result_cache) is not list` and `type(negate) is not bool`, both exact-type proofs reached
  before anything consults the value. The `negate` check is the first statement after the
  `negate, args, kwargs = deferred` unpack, and `~predicate if negate else predicate` - the only
  truth test of that slot - is further down the same helper.
- **Hot-path number exists and reproduces.** Re-ran the recorded command
  `uv run pytest -n0 docs/builder/temp-tests/050/row_carry/test_hotpath_admission.py --no-cov -q -s`:
  `patrons=2 plain_manager=2 from_queryset=2 ... plain_rows=[3, 3] from_queryset_rows=[3, 3]`,
  `patrons=3 plain_manager=2 from_queryset=2 ... rows=[3, 3, 3]` both arms, and
  `iterations=50 plain_manager_median_ms=0.780 from_queryset_median_ms=0.982 delta_ms=0.201`
  against the build report's +0.210 ms and Worker 3's +0.210 ms - the same metric on both sides,
  reproducible, and inside run-to-run noise. Whether +0.2 ms per request buys the refusal becoming
  parity is the maintainer's call and no worker's.
- **Floor run recorded with resolved versions, and the shared `.venv` is unmutated.** Read, not
  recalled: `uv pip list --python <scratch>/dsf-floor/bin/python` gives `django 5.2.16`,
  `strawberry-graphql 0.316.0`, `django-filter 25.2`, `pytest 9.1.1`,
  `django-strawberry-framework 0.0.15` (editable, this checkout), interpreter `Python 3.10.19` -
  the floor `docs/builder/BUILD.md` `## Floor verification` states, and the versions the build
  report records. `uv pip list` in the repo reads `django 6.1`, `strawberry-graphql 0.324.0`,
  `pytest-django 4.14.0`: the shared environment still carries the newest supported versions, so
  nothing was installed into it.
- **Staged anchors:** `git grep -n 'TODO(spec-050'` returns no source anchor; the single hit is a
  sentence inside an archived build plan, not an anchor.
- **Spec reconciliation:** four edits, recorded under `### Spec changes made (Worker 1 only)`.
  `uv run python scripts/check_spec_glossary.py --spec docs/spec-050-list_field_arguments-0_0_15.md`
  - OK, 43 terms. `uv run python scripts/check_citations.py --check` - OK, 1104 citations resolve.
- **Concurrent work, stop-and-report rather than revert.** Three paths went dirty during this pass
  and are in no cohort's writable set: `tests/mutations/test_resolvers.py` (670 deletions),
  `examples/fakeshop/test_query/test_library_api.py` (+239) and
  `examples/fakeshop/test_query/test_products_api.py` (+138) - a concurrent session relocating
  package rows into the live example suites. Two of them are inside Cohort A's declared ownership
  list but carry no hunk of this cohort's, and their content is unrelated to the carry or the
  admission. None was touched or reverted. The focused runs recorded above were taken before those
  hunks landed, so they do not cover them; the final gate's full sweep on one identified tree is
  what will.
- **Final status:** `revision-needed`. One source-touching Low is owed and is dispatched below with
  its exact replacement text; everything else in this cohort is accepted. The spec edits below
  stand whatever the builder pass does - none of them changes a contract Worker 2 implemented
  against, so no re-pass is owed for them.

### Summary

The raw-list seam carries a source's fetched rows onto the rebuild, so an evaluated exact queryset
and an evaluated project queryset class are both windowed from the rows they already hold at zero
further queries, and the sealer admits the pending reverse-relation predicate Django leaves on
every relation queryset whatever class built it - baking it onto the detached clone through the
unbound `Query.add_q` for every candidate, while a deferred-filter state Django never writes,
the `negate` slot's exact `bool` included, fails closed with the typed `ConfigurationError`. A
`Manager.from_queryset` relation under a prefetching plan costs the absolute 2 queries Django's
own manager costs, at two parent cardinalities and with an identical payload, and answers the same
rows on the async transport. One new boundary, pinned at 5 rows; the admission widening pinned at
9 across both tiers.

### Low dispositions

1. **`revision-needed`, one bundled builder pass: `bounded_rows`'s public docstring promises a SQL
   `LIMIT` for a shape that takes a list slice.** Measured rather than read
   (`<scratch>/w1probe/test_limit_probe.py`, `bounded_rows` under `max_list_rows=2` over four
   sources): an unevaluated exact `QuerySet` returns a `QuerySet` with `high_mark=2`; an
   unevaluated subclass returns a `QuerySet` with `high_mark=2`; an **evaluated** exact `QuerySet`
   and an **evaluated** subclass each return a plain `list` with no SQL `LIMIT` at all. Two
   sentences in that docstring state the contrary without qualification, and the paragraph's own
   categories - "a `QuerySet`" versus "a value that is already a materialized sequence ... or
   Django's prefetch cache" - no longer partition the cases, because an evaluated queryset is
   described by the first and behaves like the second. The subclass sentence is falsified by this
   cohort's carry; the exact-queryset sentence is pre-existing at HEAD, sits three lines above it
   in the same paragraph, and states the same falsehood, so fixing one and leaving the other is the
   partial-claim-fix defect (`START.md` "Instruments that lie"). `bounded_rows` is in
   `resource_policy.py`'s `__all__`, so this is a public contract statement, not an internal note.

   **Exact replacement for Worker 2**, in `django_strawberry_framework/resource_policy.py`, the
   docstring of `bounded_rows`. Replace

   > A ``QuerySet`` is bounded by SLICING, so it carries the bound into SQL as
   > ``LIMIT`` and is never evaluated unbounded; a value that is already a
   > materialized sequence (a consumer resolver's return, or Django's prefetch
   > cache) is truncated in Python, which cannot un-fetch those rows but does
   > stop the response from serializing them.

   with

   > An unevaluated ``QuerySet`` is bounded by SLICING, so it carries the bound
   > into SQL as ``LIMIT`` and is never evaluated unbounded; a value whose rows
   > are already fetched - a materialized sequence, a consumer resolver's return,
   > Django's prefetch cache, or a queryset the consumer evaluated - is windowed
   > in Python from the rows it holds, which cannot un-fetch them but does stop
   > the response from serializing them and costs no second query.

   and replace

   > A ``QuerySet``
   > subclass is the one shape that is rebuilt rather than reclassified: it is
   > sealed into a plain framework-owned queryset and sliced there, so it keeps
   > the SQL ``LIMIT`` a counted truncation would lose, or fails closed with a
   > typed ``ConfigurationError`` when its state cannot be rebuilt.

   with

   > A ``QuerySet``
   > subclass is the one shape that is rebuilt rather than reclassified: it is
   > sealed into a plain framework-owned queryset and sliced there, so an
   > unevaluated one keeps the SQL ``LIMIT`` a counted truncation would lose and
   > an evaluated one is windowed from the rows the rebuild carried forward; a
   > state that cannot be rebuilt fails closed with a typed ``ConfigurationError``.

   No behavior change, no test expectation change, no new boundary, so the pass owes no failability
   proof - it owes the inverse proof shape for a docstring-only edit (`START.md` "Instruments that
   lie": AST identity with docstrings stripped, with a string-literal control as well as a
   structural one). `django_strawberry_framework/resource_policy.py::_windowed_rows` carries the
   same unqualified subclass sentence and is **accepted as written**: the paragraph this cohort
   added sits immediately beneath it and scopes it, and the surface is package-private.

2. **Accepted: the artifact's `### Spec slice checklist (verbatim)` contradicted itself and was no
   longer verbatim.** Repaired above - the rows are re-quoted from the spec as amended, the
   superseded build-pass paragraph is replaced by a clause-by-clause tick warrant, and both ticks
   are true.

3. **Accepted with a spec edit: the rationale's "all five shipped `_SealPolicy` values".** Seven
   are constructed at module level (`django_strawberry_framework/utils/querysets.py:2794`, `:2800`,
   `:2805`, `:2808`, `:2814`, `:2816`, `:2826`); the probe exercised five. Rewritten to name the
   five by symbol rather than to assert a population, with the reason the unexercised two cannot
   differ. See `### Spec changes made (Worker 1 only)`.

4. **Routed, not remediated: the robustness row.** See `### Notes for Worker 1 (routing decisions,
   Worker 1)` below.

### Notes for Worker 1 (routing decisions, Worker 1)

- **Recorded in the DONE record's catalog (it never reached `BACKLOG.md`), owner `maintainer` - an exact `QuerySet` carrying a foreign
  `_result_cache` bypasses the raw-list ceiling.** Worker 3 measured it with
  `docs/builder/temp-tests/050/row_carry/test_w3_exact_cache.py`: an exact `models.QuerySet` whose
  `_result_cache` holds a non-list object returns 25 rows through `bounded_rows` under a
  `max_list_rows` of 2, because `normalized_row_source` returns an exact queryset unchanged,
  `_bounds_by_its_own_slice` answers True on the container's exact type, and
  `QuerySet.__getitem__` then delegates the slice to that object's own subscript. The new refusal
  at `django_strawberry_framework/utils/querysets.py:3318` lives inside `_seal_or_defect`, which an
  exact queryset never reaches.

  **The three conditions of `AGENTS.md` rule 35, written out, and which one fails.** (a) *The
  contract row it breaks* - present: `## Definition of done` #"No raw-list row source decides its
  own ceiling". (b) *A feasible project shape under supported public API* - present but only
  barely: a project would have to assign `QuerySet._result_cache`, a private Django slot, which no
  supported public API writes. (c) *The wire or configuration input that reaches it* - **this is
  the condition that fails, and it fails outright.** No document, variable, header, upload or
  settings value can put a non-list into that slot; only in-process application Python can, and
  `GOAL.md` `## Trust boundary` places application Python inside the trusted party. With (c)
  absent it is a robustness row, never a release blocker, and it is additionally **pre-existing at
  HEAD** - the code path is byte-identical there and this cohort's diff changes only
  `normalized_row_source`'s docstring - so it is neither introduced nor worsened here. It is
  recorded rather than dropped because whether the package proves the shape of a private slot a
  trusted caller wrote, when it already proves it one branch over, is a contract-level question
  the maintainer owns. If the answer is yes, the fix belongs in `normalized_row_source`, not in the
  sealer. Not remediated in this card (Decision 22).

- **Re-confirmed as routed, owner `maintainer`: the two archived specs' one-word fix.** Both
  sentences are live and unedited at this HEAD -
  `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` #"unresolved deferred filter, unsealable
  prefetch child" and `docs/SPECS/spec-034-permissions-0_0_10.md` #"an unresolved deferred filter"
  - and both are made imprecise by the admission change: after it, only a MALFORMED deferred filter
  is unsealable. "unresolved" becomes "malformed" in both. Amending a shipped spec is a round over
  that spec (`docs/builder/BUILD.md` `### Cohorting, naming, and closure`), not a slice edit, and
  neither file is in any cohort's writable set, so neither is touched here.

- **Re-confirmed as routed, owner `maintainer`, and still a paste: the `docs/GLOSSARY.md` "Sealed
  execution queryset" body.** The exact replacement paragraph in this artifact's
  `### Notes for Worker 1 (spec reconciliation)` is still valid against the CURRENT render - I
  matched the quoted old text against `docs/GLOSSARY.md` with whitespace normalized and it occurs
  exactly once. The glossary is DB-backed: edit the `GlossaryTerm` body through the ORM and
  regenerate, because a hand edit to the rendered file is reverted by the next render and goes red
  in CI's generator `--check`. It belongs to Worker 0's card-close board/glossary pass.

- **Re-confirmed as routed, owner `maintainer`: `_UNRECOMPOSED_CHILD_POLICY` has no production
  reader.** `git grep -n '_UNRECOMPOSED_CHILD_POLICY' -- '*.py'` returns its own definition
  (`django_strawberry_framework/utils/querysets.py:2805`), two docstring mentions in the same
  module, and one test row (`tests/utils/test_querysets.py:5035`) - no production call site, since
  commit `fd39cac6` moved `optimizer/walker.py::_build_child_queryset` onto
  `_PREFETCH_CHILD_POLICY`. `_SealPolicy`'s `reject_sliced` bullet still names the optimizer
  walker's nested-connection child as a surface it is off for. The cause is a concurrent session's
  committed change to a file in no cohort's writable set, and the resolution is a delete-or-correct
  choice about dead code, so it is the maintainer's and not this cohort's.

- **Recorded, no action: the spec's `## Test plan` and its Slice 3 / DoD rows name
  `QuerySet.as_manager()` and `Manager.from_queryset` for one Django shape.** The test plan now
  says so in one sentence, so the two homes cannot be read as two requirements.

### Spec changes made (Worker 1 only)

1. `docs/spec-050-list_field_arguments-0_0_15.md` `### Decision 8`, the paragraph closing the
   evaluation-carry contract (lines 1292-1301 as edited). The sentence "Every other seal keeps its
   `require_unevaluated` verdict: a visibility hook's input and result and an `OrderSet.apply_*`
   result are still refused when evaluated" is false for the visibility seals and was escalated as
   Worker 3's Medium. Measured at the code, not read from a docstring: `require_unevaluated=True`
   appears on `_ORDERSET_RESULT_POLICY` (at `f7192bfb`; now `_SIDECAR_RESULT_POLICY`, which also seals `FilterSet.apply_*` returns) alone
   (`django_strawberry_framework/utils/querysets.py:2816`); the other six `_SealPolicy` values
   leave it `False`, and `tests/utils/test_querysets.py` seals an evaluated source at the
   visibility boundary in **zero queries** while asserting both the hook's input and the returned
   result carry `_result_cache is None`. Rewritten as a current statement of the true contract: the
   refusal axis is on for the post-`OrderSet` result seal alone, a visibility seal admits an
   evaluated source and drops its cache in the rebuild on input and result alike, and the
   `get_queryset` contract is shared with the Relay node, connection and relation surfaces, so
   holding it stricter here would make one hook's verdict depend on which field called it.
   **Five-homes sweep for the same claim: one home only.** `grep -n
   'require_unevaluated\|refused when evaluated\|when evaluated\|arrives evaluated\|evaluated
   source'` plus a full `grep -n 'evaluat'` over the spec returns the Decision 8 paragraph and
   nothing else asserting it; every other occurrence (`## Slice checklist` line 105,
   Decision 5 step 4, `## Test plan` line 2103 and 2311, `## Definition of done`'s
   `OrderSet.apply_*` row) is correctly scoped to the post-`OrderSet` result seal and stands
   unedited. The same sweep over the rationale returns nothing. Triggered by the close cycle,
   Cohort A.
2. Same file, `## Definition of done`, the "A source that arrives evaluated" row (lines 2832-2838
   as edited). "at the same ABSOLUTE query count ... on both transports" reads as owing the
   absolute count on the async transport, which the same spec's `## Test plan` explicitly does not
   ask for and which no row can honestly assert - a `CaptureQueriesContext` opened on the calling
   thread cannot see the ORM work a `sync_to_async` worker thread does, so an empty capture is
   indistinguishable from a green zero. Two homes disagreeing is a defect
   (`START.md` "Five homes per contract"). The row now owes the absolute count at two parent
   cardinalities and the same rows on the async transport, and names why. Triggered by the close
   cycle, Cohort A.
3. Same file, `## Test plan` -> `### The raw-list row source`, the probe-schema sentence (lines
   2598-2603 as edited). It required "the optimizer as a class entry", a spelling
   `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`
   forbids across every first-party `.py` under `spec-029` Decision 3 - Strawberry resolves a
   non-instance entry once per operation, so a bare class hands every request a cold plan cache.
   The full sweep failed on it and the implementation landed the singleton-behind-a-factory
   spelling, one per arm, which preserves the property the spec actually needs (separate plan
   caches, so the control is a control) while satisfying the governance gate. The spec stated the
   forbidden spelling as a requirement; it now states the property and names the prohibition. A
   `[spec-029]` reference-style link definition was added to the bottom block in the same edit.
   Triggered by the close cycle, Cohort A, Worker 2's amendment and Worker 3's seconding.
4. `docs/spec-050-list_field_arguments-0_0_15-rationale.md` `### Decision 8`, the measured fact
   behind the pending-predicate admission (lines 322-333 as edited). "all five shipped
   `_SealPolicy` values" states a population the probe did not measure: seven values are
   constructed at module level (at `f7192bfb`; at HEAD `_UNRECOMPOSED_CHILD_POLICY` is retired by
   `4d9f1c3d` and `_LIST_RELATION_CHILD_POLICY` is added) (`django_strawberry_framework/utils/querysets.py:2794`, `:2800`,
   `:2805`, `:2808`, `:2814`, `:2816`, `:2826`) and the probe covered five, omitting
   `_CASCADE_SEAL_POLICY` and `_UNRECOMPOSED_CHILD_POLICY`. Rewritten to name the five exercised
   values by symbol - a closed list that cannot rot into a wrong count - plus the reason the
   unexercised two cannot have differed: the deleted gate read the candidate's class and no field
   of the policy at all. Triggered by Worker 3's Low.

Gates run over the edited paths: `uv run python scripts/check_spec_glossary.py --spec
docs/spec-050-list_field_arguments-0_0_15.md` - OK, 43 terms;
`uvx pre-commit run --files docs/spec-050-list_field_arguments-0_0_15.md
docs/spec-050-list_field_arguments-0_0_15-rationale.md docs/builder/bld-050-close-row_carry.md`;
`uv run python scripts/check_citations.py --check` - OK, 1104 citations resolve.

---

## Build report (Worker 2, pass 3)

Applies the one source-touching Low dispatched by `## Final verification (Worker 1)`
`### Low dispositions` item 1: `bounded_rows`'s public docstring promised a SQL `LIMIT` for two
shapes that take a Python window. Docstring text only; no executable line moved.

### Precondition

`git diff HEAD -- django_strawberry_framework/resource_policy.py` before any edit: one hunk,
`5 insertions(+)`, the pass-1 docstring paragraph added to
`django_strawberry_framework/resource_policy.py::_windowed_rows` (`#"A source that arrives
evaluated is windowed"`). No other hunk, so the file carried only pass-1 docstring work as the
dispatch requires.

### Files touched

- `django_strawberry_framework/resource_policy.py` - the `bounded_rows` docstring only. Both
  dispatched sentences replaced verbatim. `git diff HEAD --stat` moves from `5 insertions(+)` to
  `23 insertions(+), 15 deletions(-)`: 11 lines of dispatched replacement text, and 7 lines of the
  intervening sentence re-wrapped with its wording unchanged, because the first replacement ends
  mid-line in the original and would otherwise strand `#"Which operation does the truncating"` on a
  39-column line. No citer quotes any of the re-wrapped text - `git grep` for
  `#"Which operation does the truncating"`, `#"counted into a fresh list instead"` and
  `#"comes back as a bounded list of its keys"` returns only the three source lines themselves, and
  no `resource_policy.py #"..."` citation exists anywhere in the tree.

### Sentences written

Replacing the unqualified `QuerySet`-versus-materialized-sequence sentence:

> An unevaluated ``QuerySet`` is bounded by SLICING, so it carries the bound
> into SQL as ``LIMIT`` and is never evaluated unbounded; a value whose rows
> are already fetched - a materialized sequence, a consumer resolver's return,
> Django's prefetch cache, or a queryset the consumer evaluated - is windowed
> in Python from the rows it holds, which cannot un-fetch them but does stop
> the response from serializing them and costs no second query.

Replacing the unqualified subclass sentence:

> A ``QuerySet``
> subclass is the one shape that is rebuilt rather than reclassified: it is
> sealed into a plain framework-owned queryset and sliced there, so an
> unevaluated one keeps the SQL ``LIMIT`` a counted truncation would lose and
> an evaluated one is windowed from the rows the rebuild carried forward; a
> state that cannot be rebuilt fails closed with a typed ``ConfigurationError``.

Both are the dispatched wording character for character; the only editorial act was the re-wrap of
the sentence that sits between them, whose words are unchanged.

### The `bounded_rows_async` check the dispatch asked for

**No correction owed; nothing edited there.** `django_strawberry_framework/resource_policy.py::bounded_rows_async`
does not carry the unqualified promise. Its one `LIMIT` sentence is
`#"``LIMIT`` instead of being materialized through the async iterator"`, whose subject is
**`lazy` querysets** - "Synchronous iterables (including Django ``QuerySet`` objects, which expose
both protocols) stay on ``bounded_rows`` so lazy querysets retain their SQL ``LIMIT``". `lazy`
already names the unevaluated case, which is exactly the qualification the dispatched replacement
introduces, and the sentence is about which surface a source is routed to rather than about what
every queryset gets. An evaluated queryset is not lazy, so the sentence makes no claim about it and
is true as written.

Read from the file rather than recalled: `grep -n LIMIT
django_strawberry_framework/resource_policy.py` returns 9 prose occurrences. Three sit on
package-private surfaces and are out of this dispatch's scope, and Worker 1 accepted the
`_windowed_rows` one explicitly - `#"carries the bound into SQL as ``LIMIT``, so a queryset is
never evaluated"` on the `_SLICE_BOUNDED_ROW_TYPES` comment, `#"among them the ``QuerySet`` whose
slice is what pushes ``LIMIT`` into SQL"` and `#"``LIMIT`` in SQL and an unsealable one fails
closed"` in `django_strawberry_framework/resource_policy.py::_windowed_rows`, which the pass-1
paragraph immediately beneath scopes. The remaining occurrences are the
`RESOURCE_LIMIT_ERROR_CODE` identifier, not prose.

### Tests added or updated

None. A docstring carries no assertion, and the dispatch states no behavior, expectation, or
boundary changes.

### Validation run

- `uv run ruff format django_strawberry_framework/resource_policy.py` - **1 file left unchanged**.
- `uv run ruff check --fix django_strawberry_framework/resource_policy.py` - **All checks passed!**
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/resource_policy.py`
  - exit 0, silent (ASCII-only holds: the replacement uses `-`, never an en or em dash).
- `uvx pre-commit run --files django_strawberry_framework/resource_policy.py` - all six hooks
  **Passed** (kanban tracked path constants, source layout, ruff format, ruff check, kanban
  anchors, citations).
- `uv run python scripts/check_citations.py --check` - **OK: 1107 citations resolve** (928 in 448
  `.py` files, 179 in `KANBAN.md`).
- `uv run pytest -n0 tests/test_resource_policy.py --no-cov -q` - **288 passed** in 4.97s, exit 0.
  No `--cov*` flag.
- `git status --short` after both ruff invocations: `django_strawberry_framework/resource_policy.py`
  is the only path of mine. **Stop-and-report, not a revert:** five paths went dirty during this
  pass that no cohort owns and that carry no hunk of mine -
  `tests/mutations/test_fields.py`, `tests/mutations/test_inputs.py`,
  `tests/mutations/test_operations.py`, `tests/mutations/test_permissions.py` and
  `tests/mutations/test_sets.py`, alongside the `tests/mutations/test_resolvers.py`,
  `examples/fakeshop/test_query/test_library_api.py`,
  `examples/fakeshop/test_query/test_products_api.py`, `docs/feedback.md` and
  `examples/fakeshop/db.sqlite3` that final verification already recorded. The same concurrent
  session is still relocating package rows into the live suites. None was read for content, touched,
  or reverted.

### Failability proofs

None; this pass introduced no new boundary. A docstring-only edit owes the **inverse** proof
instead - stripped-AST identity against `git show HEAD:` - and a proof with no control is an
assertion that cannot fail, so it carries three.

Script: `<scratch>/ast_identity.py`, which writes `<scratch>/resource_policy.HEAD.py`,
`<scratch>/resource_policy.WORK.py`, `<scratch>/ast.HEAD.txt` and `<scratch>/ast.WORK.txt`. It
parses both sources, deletes the leading string `Expr` of every `Module`, `ClassDef`,
`FunctionDef` and `AsyncFunctionDef`, and compares `ast.dump(..., include_attributes=False)`.

| Row | Result | What it establishes |
|---|---|---|
| `files byte-identical` | **False** | the edit exists; identity below is not measuring an unmodified file |
| `stripped-AST identical` | **True** | no executable line, constant, signature or default changed |
| control, structural | **True** (digests differ) | appending `_CONTROL_SENTINEL = 1` moves the digest, so the comparison can fail |
| control, string literal | **True** (digests differ) | rewriting the non-docstring literal `"RESOURCE_LIMIT_EXCEEDED"` moves the digest, so the stripper deletes docstrings only and is not blind to every string |
| un-stripped `HEAD` vs work | **False** (digests differ) | the stripper is what makes the two equal, so the identity is not vacuous |

### Hot-path budget

Not applicable; plan declares no hot path, and this pass changes no executable line.

### Floor verification

Owned by the final gate per the plan's declaration; a docstring carries no version-sensitive
behavior in any case.

### Implementation notes

- **The re-wrap is the only judgement in this pass.** The first dispatched replacement ends with a
  full stop where the original ended mid-line, so the sentence that follows had to start somewhere.
  Joining it to the replacement's last line reaches 101 columns; leaving it alone gives a 39-column
  line inside a paragraph wrapped at ~78. Re-wrapping those seven lines at the paragraph's own
  width, with the words untouched, is the only option that leaves both the dispatched text verbatim
  and the paragraph readable. The proof that this is safe is the grep above, not the judgement.
- The two replacements are separated by unchanged prose, so they were applied as one edit over the
  whole paragraph rather than two; the diff above is what shows the intervening text is a re-wrap
  and not a rewrite.

### Notes for Worker 3

- The pass is prose-only. The instrument that matters is the stripped-AST table, not the test run:
  288 passing rows would pass identically against a docstring saying anything at all, which is why
  the identity proof carries its own controls.
- `django_strawberry_framework/resource_policy.py::_windowed_rows` and the
  `_SLICE_BOUNDED_ROW_TYPES` comment still carry unqualified `LIMIT` prose on package-private
  surfaces. That is Worker 1's recorded acceptance in `### Low dispositions` item 1, not an
  oversight of this pass.

### Notes for Worker 1 (spec reconciliation)

- No spec gap surfaced. The dispatched replacement describes exactly what the carry shipped, and
  `docs/spec-050-list_field_arguments-0_0_15.md` Decision 8 as amended already carries the
  evaluated-source case.
- The `bounded_rows_async` check the dispatch requested came back negative, with the reason recorded
  above under `### The bounded_rows_async check the dispatch asked for`. If the intent was that
  every surface naming `LIMIT` should name the unevaluated case explicitly - including the
  package-private `_windowed_rows` and `_SLICE_BOUNDED_ROW_TYPES` prose that item 1 accepted - that
  is a wider dispatch than the one written and would need a re-pass to say so.

---

## Review (Worker 3, pass 3)

Short re-review of the one source-touching Low dispatched by `## Final verification (Worker 1)`
`### Low dispositions` item 1. Docstring-only pass, so the two questions are: is the text the
dispatched text, and is it true of the code. Both answered mechanically.

### The dispatched wording, compared machine-to-machine

Not read side by side. Both dispatched blockquotes were cut out of this artifact by line span
(2342-2347 and 2359-2364), un-quoted, whitespace-flattened, and counted against the
whitespace-flattened working file and against `git show HEAD:django_strawberry_framework/resource_policy.py`:

| Row | Count | What it establishes |
|---|---|---|
| replacement 1 in WORK | 1 | the dispatched sentence is present, once, character for character |
| replacement 2 in WORK | 1 | same |
| replacement 1/2 in HEAD | 0 / 0 | the text is new, so the count above is not reading unchanged prose |
| original 1 in HEAD, original 2 in HEAD | 1 / 1 | the dispatch quoted the file accurately |
| original 1/2 still in WORK | 0 / 0 | no half-applied edit, no duplicated paragraph |
| intervening sentence, WORK vs HEAD after flatten | identical | the re-wrap changed line breaks only; not one word moved |

Worker 2's own quoted copies of both replacements (artifact lines 2538-2543, 2547-2552) are
byte-equal to Worker 1's dispatch, so the build report is not quoting a second variant.
Replacement 2 does not match line-for-line, and cannot: the dispatch quotes it starting mid-line
(`A ``QuerySet``` is the tail of the preceding line), which is why the comparison above is on
flattened text rather than on lines.

### The sentences against the code, measured

`docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py`, five rows, `bounded_rows` under
`ResourcePolicy(max_list_rows=2)` over fakeshop `Category` (`seed_data(6)`; the catalog is 25 rows,
which is why the row asserts `len(fetched) > 2` rather than a seeded cardinality):

| Source | Result | Which clause it grades |
|---|---|---|
| unevaluated exact `QuerySet` | `type is QuerySet`, `query.high_mark == 2`, 2 rows | "An unevaluated ``QuerySet`` is bounded by SLICING, so it carries the bound into SQL as ``LIMIT``" |
| unevaluated no-override `QuerySet` subclass | `type is QuerySet` (rebuilt), `high_mark == 2`, 2 rows | "an unevaluated one keeps the SQL ``LIMIT`` a counted truncation would lose" |
| evaluated exact `QuerySet` | `type is list`, equals `fetched[:2]`, **0 queries** | "a queryset the consumer evaluated - is windowed in Python from the rows it holds ... costs no second query" |
| evaluated subclass | `type is list`, equals `fetched[:2]`, **0 queries** | "an evaluated one is windowed from the rows the rebuild carried forward" |
| control | unevaluated exact queryset inside the same counter: **1 query**, its SQL contains `LIMIT 2` | the zero-query rows above use an instrument that can report non-zero, and the `LIMIT` is in the emitted SQL, not only in `high_mark` |

`CaptureQueriesContext` forces the debug cursor, so the zero counts are measurements rather than a
disabled counter; the control is what proves it. Both evaluated rows also pin the window as the
LEADING one (`fetched[:2]`, the source's own `order_by("pk")` order), not merely two rows.

`examples/fakeshop/db.sqlite3` md5 `2732e633f3303c55aac9d9f398e48df7` before and after every run in
this pass, including the two gate runs below: identical. The probe is a `django_db` test on the
per-worker test database and writes nothing tracked.

### `bounded_rows_async`: no edit owed, confirmed independently

Read from the file, not from the build report. The only `LIMIT` sentence on that surface is
`#"stay on ``bounded_rows`` so lazy querysets retain their SQL ``LIMIT``"`, whose subject is
`lazy` querysets and whose predicate is which surface a source is routed to. `lazy` already excludes
the evaluated case, so the sentence makes no claim the carry falsifies. Worker 2's conclusion is
correct and its reasoning is the reasoning.

### The diff is docstring-only, proved two ways

Written to `<scratch>`, never obtained by checkout: `git show HEAD:...` -> `<scratch>/rp.HEAD.py`,
working copy -> `<scratch>/rp.WORK.py`.

| Row | Result | What it establishes |
|---|---|---|
| files byte-identical | False | an edit exists; the identity below is not measuring an unmodified file |
| stripped-AST identical (leading string `Expr` of every `Module`/`ClassDef`/`FunctionDef`/`AsyncFunctionDef` deleted) | **True** (`e3e8206...` both) | no executable line, constant, signature or default changed |
| un-stripped HEAD vs WORK | False | the stripper is what makes them equal; the identity is not vacuous |
| control, structural (`_CTRL=1` appended to the WORK copy) | differs | the comparison can fail on a statement |
| control, string literal (`"RESOURCE_LIMIT_EXCEEDED"` rewritten in the WORK copy) | differs | the stripper removes docstrings only; it is not blind to every string |
| control, inverse (a non-edited docstring mutated in the WORK copy) | still identical | the stripper really is deleting docstrings, so the True row above is the claim it looks like |

Independently of the AST: all 23 added lines were mapped to line spans of docstring nodes in the
working file. Zero fall outside one; the two owners are `_windowed_rows` and `bounded_rows`. So the
diff carries no comment change either, which an AST comparison could not have seen.

### No process provenance, and the citation surface

- Added lines swept for provenance vocabulary (`previously`, `as of`, slice/pass/worker/round/review,
  severity labels, `spec-0`, `TODO`): no hit. (`Low` matches inside `follows`; that is the regex, not
  a label.)
- ASCII-only holds on every added line; longest added line is 82 columns.
- Citation sweep run independently of Worker 2's list: `resource_policy.py #"..."` appears nowhere in
  the tree outside this artifact's own prose (the two other hits name `extensions/resource_policy.py`,
  a different path). Control: 126 `.py #"` citations exist in tracked `.py`/`.md`, so the pattern
  finds what is there.
- One correction to the build report's grep claim, no consequence: after the re-wrap
  `#"comes back as a bounded list of its keys"` is no longer on one source line (the file now breaks
  after `comes back as`), so that phrase is not citable as a single-line substring at all. Nothing
  cites it, so nothing is stranded; recorded so a later citer does not quote it from this artifact.

### High:

None.

### Medium:

None.

### Low:

#### 1. The sentence between the two replacements still says an evaluated queryset "keeps its type"

`django_strawberry_framework/resource_policy.py:1063-1070`, the clause "an exact ``list``,
``tuple``, ``str``, ``bytes``, ``bytearray`` or ``QuerySet`` is sliced and keeps its type". Measured
above: an evaluated exact `QuerySet` comes back as a `list`. The clause's real subject is which
OPERATION applies - slice versus count - and that half is true for every listed type; the trailing
"keeps its type" is the half the carry falsified, one sentence away from the two the dispatch
replaced, in the paragraph the dispatch curated. Its words are unchanged from HEAD (Worker 2
re-wrapped the lines only, correctly), and the replacement immediately above it now tells a reader
in order that an evaluated value "is windowed in Python from the rows it holds", which scopes it.

Not blocking, and **not** a fix Worker 2 may invent: the exact wording of this paragraph is Worker
1's dispatched text. Escalated below.

#### 2. Two parallel sites outside this file carry the same unqualified promise

Both found by sweeping the claim's vocabulary across tracked `.md` (population 217), not by reading
the diff's file list:

- `docs/GLOSSARY.md:678`, the `0.0.14` row-bound entry: "so a `QuerySet` carries it into SQL as a
  `LIMIT` / `OFFSET`". Consumer-facing and rendered from the fakeshop glossary DB, so the fix is a
  DB edit plus a render, which no cohort in this cycle owns.
- `docs/SPECS/spec-047-resource_policy-0_0_14.md:795`: "is truncated in Python" versus "a `QuerySet`
  carries it into SQL as a `LIMIT`". Archived, and true on its own date - the carry shipped after it.

Neither is editable under this dispatch. Routed, not remediated; see the notes below.

### DRY findings

None. The pass adds no code, no literal and no helper. The one judgement in it - re-wrapping the
intervening sentence rather than leaving a 39-column line or a 101-column one - is the minimum edit
that keeps the dispatched text verbatim, and the grep above is what makes it safe rather than the
judgement.

### Failability audit

The pass introduces no boundary, so the mandatory re-run floor is met by an empty re-run set
(`worker-3.md`: "An empty re-run set is legal only when the diff introduces no boundary that meets
the floor"). What it owes instead is the inverse proof, which I re-derived from scratch rather than
re-reading Worker 2's table; my three controls include one Worker 2 did not run (mutating a
docstring OTHER than the edited one must leave the stripped digests equal - otherwise a "True"
identity row would prove nothing about docstrings).

### Hot-path budget

Not applicable; plan declares no hot path, and the stripped-AST identity is the proof that no
executable line moved.

### Floor verification

Owned by the final gate per the plan's declaration. A docstring carries no version-sensitive
behavior.

### Test staleness sweep, run independently of the diff's file list

- No test in any of the four trees reads `bounded_rows.__doc__` or asserts docstring text, so no
  permanent expectation can rot on this pass (`__doc__` hits in the tree are a type factory's
  attribute dict, an `assigned=` tuple, and `argparse` descriptions).
- The old wording survives nowhere in first-party `.py`.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty: `__all__` and the re-export
list are unchanged. `bounded_rows` was already exported from `resource_policy.py`; this pass changes
its prose, not the surface.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The two documentation
sites named under Low 2 are untouched by this diff, which is the finding.

### Gates

- `uvx pre-commit run --files django_strawberry_framework/resource_policy.py` - all six hooks
  **Passed**.
- `uv run python scripts/check_citations.py --check` - **OK: 1108 citations resolve** (929 in 448
  `.py` files, 179 in `KANBAN.md`). One more than the build report's 1107/928; the extra citation is
  in a concurrent session's file, not in this diff, whose 23 added lines contain no `::Symbol`.
- `uv run pytest -n0 tests/test_resource_policy.py --no-cov -q` - **288 passed**, exit 0, no `--cov*`
  flag. As Worker 2 says, this run is not the instrument for a prose pass; it is the regression
  backstop.
- `git status --short`: `django_strawberry_framework/resource_policy.py` is the only path this pass
  owns. The concurrent session's churn has grown again since the build report (`docs/TREE.md` and
  `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` are now dirty too, and
  `docs/bug_hunt/bug_hunt-0_0_15.md` is deleted with `bug_hunt-0_0_1555.md` untracked). Reported, not
  read for content, not touched, not reverted.

### What looks solid

- The pass applied a dispatch and did nothing else, and it is checkable that it did nothing else:
  stripped-AST identity plus the added-lines-inside-docstring-spans map leave no room for a rider.
- The `bounded_rows_async` answer is a real reading of the sentence's subject rather than a
  no-hits grep, and it survives an independent read.
- The re-wrap is disclosed as a re-wrap, with the evidence (word-identical intervening text) that
  distinguishes it from a rewrite.

### Temp test verification

- `docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py` - five rows, all passing, four
  grading the dispatched clauses and one a positive control on the query counter. Gitignored scratch.
- Disposition: **not promoted.** Every behavior it measures is already pinned permanently -
  `tests/test_resource_policy.py::test_an_exact_queryset_still_carries_the_row_bound_into_sql` and
  `::test_a_sealable_queryset_subclass_keeps_the_row_bound_in_sql` for the unevaluated rows, and this
  cohort's own evaluated-carry rows for the rest. It caught no bug; it graded prose.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: Low 1, the "keeps its type" clause.** Resolution paths, in the order I would weigh
  them. (a) Leave it: the replacement above it scopes the paragraph for a reader taking it in order,
  and the clause's operative half - slice versus count - is true for every type it lists. (b) Dispatch
  a third one-clause replacement narrowing it to the unevaluated case (e.g. "... is sliced, and an
  unevaluated one keeps its type"). It is your paragraph and your call; Worker 2 must not invent
  wording here, which is why this is escalated rather than sent back.
- **Escalated: Low 2, the two parallel sites.** `docs/GLOSSARY.md:678` is consumer-facing and
  rendered from the glossary DB, so it needs an ORM edit plus `build_glossary_md.py` in whatever
  change owns it - the same class of item as the still-unowned "Sealed execution queryset" body
  already recorded in this artifact's pass-2 notes, and it should probably travel with it rather than
  open a second route. `docs/SPECS/spec-047-resource_policy-0_0_14.md:795` is archived and was true on
  its own date; my reading is that it needs nothing, but it is the same sentence, so you should be the
  one to say so rather than a later sweep rediscovering it.

### Review outcome

`review-accepted`. The dispatched text is present character for character and nothing else in the
file changed; the four clauses it asserts are true as measured; `bounded_rows_async` needed no edit
and the reason holds; the three gates are green and the tracked DB is byte-identical. Both Lows are
prose in files this dispatch does not authorize a worker to write, escalated above with resolution
paths rather than held against the diff.

---

## Final verification (Worker 1, pass 2)

Scope: the pass-3 docstring dispatch, plus the two Lows Worker 3 escalated. The carry and the
admission were verified in pass 1; nothing in the pass-3 diff touches them.

- **The two dispatched sentences landed verbatim, measured rather than read side by side.** Both
  blockquotes were cut out of this artifact by line span (2342-2347, 2359-2364), un-quoted,
  whitespace-flattened, and counted against the flattened working file and against
  `git show HEAD:django_strawberry_framework/resource_policy.py` written to the scratchpad. Each
  replacement occurs **once** in WORK and **zero** times in HEAD; each original occurs **once** in
  HEAD and **zero** times in WORK, so nothing is half-applied and no paragraph is duplicated.
  Controls both ways: a nonsense needle counts 0 in WORK (the counter can miss), and an unchanged
  sentence from the same paragraph counts 1 in both (the counter can hit). Worker 2's own quoted
  copies of both replacements are byte-equal to the dispatch, so the build report is not quoting a
  second variant.
- **The sentences are true of the code.** Worker 3's temp test re-run by me:
  `uv run pytest -n0 docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py --no-cov -q`
  - **5 passed**, exit 0. Read before trusted: its evaluated rows assert `type(rows) is list`,
  `materialized == fetched[:2]` and **0** captured queries, its unevaluated rows assert
  `type(rows) is models.QuerySet` with `query.high_mark == 2`, and its control asserts **1** query
  whose SQL contains `LIMIT 2` - so the zero-query rows are measurements from an instrument that
  can report non-zero.
- **The diff is docstring-only**, proved by stripped-AST identity against `git show HEAD:` written
  to `<scratch>/w1p2/rp.HEAD.py` (never a checkout), with four controls:

  | Row | Result | What it establishes |
  |---|---|---|
  | files byte-identical | False | an edit exists; the identity is not measuring an unmodified file |
  | stripped-AST identical | **True**, `e3e820663f8e6d4f...` both | no executable line, constant, signature or default changed |
  | un-stripped HEAD vs WORK | False | the stripper is what makes them equal; the identity is not vacuous |
  | control, structural (`_CTRL_SENTINEL = 1` appended) | digest moves | the comparison can fail on a statement |
  | control, string literal (`"RESOURCE_LIMIT_EXCEEDED"` rewritten) | digest moves | the stripper deletes docstrings only, not every string |
  | control, inverse (a docstring the diff never touched, mutated) | digest unchanged | the stripper really is deleting docstrings, so the True row means what it looks like |

  The digest matches Worker 3's independently derived `e3e8206...`.
- **Gates.** `uvx pre-commit run --files django_strawberry_framework/resource_policy.py` - all six
  hooks **Passed** on the first run (no re-run needed this pass).
  `uv run python scripts/check_citations.py --check` - **OK: 1108 citations resolve** (929 in 448
  `.py` files, 179 in `KANBAN.md`). `uv run pytest -n0 tests/test_resource_policy.py --no-cov -q` -
  **288 passed**, exit 0, no `--cov*` flag.
- **Spec slice checklist:** unchanged and still both `- [x]`; the clause-by-clause tick warrant in
  `### Spec slice checklist (verbatim)` stands, because a docstring pass moves no contract. Nothing
  deferred, nothing over-ticked.
- **Concurrent work, stop-and-report.** `examples/fakeshop/db.sqlite3` md5
  `2732e633f3303c55aac9d9f398e48df7` before and after every command in this pass - identical, and
  the same value Worker 3 recorded. The concurrent session's churn is unchanged from Worker 3's
  list (`tests/mutations/*`, the two live example suites, `docs/feedback.md`, `docs/TREE.md`,
  `docs/bug_hunt/*`, `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`). None touched,
  none reverted.
- **Final status:** `revision-needed`. One clause in the same paragraph is false as written and is
  dispatched below with its exact replacement; everything else is accepted.

### Low dispositions (pass 2)

1. **`revision-needed`, one builder pass: the clause between the two replaced sentences says an
   exact `QuerySet` that is sliced "keeps its type", and an evaluated one comes back as a `list`.**
   Read whole rather than as a clause: the paragraph now opens by splitting the cases ("An
   unevaluated ``QuerySet`` is bounded by SLICING ... a value whose rows are already fetched - ...
   or a queryset the consumer evaluated - is windowed in Python"), and closes by splitting them
   again for the subclass. Between them sits an enumeration that re-merges them: "an exact
   ``list``, ``tuple``, ``str``, ``bytes``, ``bytearray`` or ``QuerySet`` is sliced and keeps its
   type". The new qualification does **not** scope it - it qualifies the *previous* sentence's
   subject, while this sentence names `QuerySet` again with no evaluation qualifier of its own and
   asserts the one thing the carry falsified: the returned type. Measured, not argued -
   `test_evaluated_exact_queryset_is_windowed_in_python_with_no_query` asserts `type(rows) is list`
   for an **exact** `models.QuerySet`, and `QuerySet.__getitem__` returns `self._result_cache[k]`
   whenever the cache is populated, so the slice answers with a list and never reaches
   `_chain()`. `bounded_rows` is in `resource_policy.py`'s `__all__`, so the return type is a
   public contract statement. Leaving it is the partial-claim-fix defect this dispatch exists to
   avoid: two sentences of one paragraph would be qualified and the sentence between them would
   still promise the opposite.

   **Exact replacement for Worker 2**, in `django_strawberry_framework/resource_policy.py`, the
   docstring of `bounded_rows`, and nothing else in the file. Replace

   > Which operation does the truncating follows from what the value IS,
   > never from whether a subscript happened to answer: an exact ``list``,
   > ``tuple``, ``str``, ``bytes``, ``bytearray`` or ``QuerySet`` is sliced and
   > keeps its type, and every other shape - a subclass of one of the sequence
   > types, a mapping, a bare iterable - is counted into a fresh list instead,
   > which is how the ceiling stays a ceiling on a sequence type whose own
   > ``__getitem__`` is consumer code. A mapping therefore still comes back as
   > a bounded list of its keys.

   with

   > Which operation does the truncating follows from what the value IS,
   > never from whether a subscript happened to answer: an exact ``list``,
   > ``tuple``, ``str``, ``bytes``, ``bytearray`` or ``QuerySet`` is sliced,
   > and every other shape - a subclass of one of the sequence types, a
   > mapping, a bare iterable - is counted into a fresh list instead, which is
   > how the ceiling stays a ceiling on a sequence type whose own
   > ``__getitem__`` is consumer code. The slice answers in the sliced value's
   > own type, except on a queryset whose rows are already fetched: there
   > ``QuerySet.__getitem__`` answers from the rows it holds, so the window
   > comes back as a ``list``. A mapping therefore still comes back as a
   > bounded list of its keys.

   Re-wrapping to the paragraph's own width is permitted and expected; the words are the contract.
   No behavior, expectation or boundary changes, so the pass owes no failability proof - it owes
   the same inverse proof shape pass 3 ran (stripped-AST identity against `git show HEAD:`, with a
   structural control, a string-literal control, and an untouched-docstring inverse control).
   `django_strawberry_framework/resource_policy.py::_windowed_rows` and the
   `_SLICE_BOUNDED_ROW_TYPES` comment remain **accepted as written**, as in pass 1: both state why
   the exact `QuerySet` is in the slice set rather than what a slice returns, the comment's own
   claim ("a queryset is never evaluated unbounded") is true in both states, and the paragraph this
   cohort added to `_windowed_rows` scopes that surface. Both are package-private.

2. **Worker 3's Low 2, the two parallel sites: routed, not remediated.** `docs/GLOSSARY.md` is
   DB-backed and in no cohort's writable set, and the archived spec is a round over a shipped spec.
   Both are written out under `### Notes for Worker 1 (spec reconciliation)` below.

3. **Five-homes sweep for the same promise, run over the four files the dispatch names.**
   Instrument: whitespace-flattened full-text counting in Python, not a per-line grep - the claim
   wraps across lines in every one of these files, and a per-line sweep reads a wrapped promise as
   absent. Population, with the verdict on each:

   | File | Hits | False as written | Verdict |
   |---|---|---|---|
   | `docs/spec-050-list_field_arguments-0_0_15.md` | 5 homes carrying the promise (`## Goals` preamble; `### Decision 8`; `## Edge cases`; `## Definition of done` raw-list row; `## Definition of done` `LIMIT/OFFSET` row) | **2** | the two DoD rows fixed below |
   | `docs/spec-050-list_field_arguments-0_0_15-rationale.md` | 3 (the card-DoD amendment note, twice; Decision 8's measured-fact paragraph) | 0 | all three are deliberation or history, and each describes a promise rather than making one |
   | `docs/README.md` | 1 (`### DjangoListField`, "a single row-bounding window (`offset:offset + limit`) slices the result last") | 0 | names the operation, not the returned type or a SQL `LIMIT` |
   | `README.md` | 0 | 0 | the pitch states the bound, never the mechanism |

   The three active-spec homes left unedited, with the reason each is true as written: the
   `## Goals` preamble ("the default policy produces a queryset high mark and therefore a
   `LIMIT`") is about the default resolver's `_default_manager.all()`, which is unevaluated by
   construction; `### Decision 8`'s "because slicing is what carries the bound into SQL as
   `LIMIT`" is the reason the operation was chosen and the decision states the evaluated rule
   explicitly in its own body ("A queryset that reaches the seam already evaluated ... is windowed
   from the rows it holds"); `## Edge cases` says a queryset "is sliced", which is true in both
   states, and makes no claim about the result. `## Test plan`'s `high_mark` sentence names the
   rows of an unevaluated control and is followed immediately by the evaluated-state paragraph.

### Notes for Worker 1 (spec reconciliation)

Two items for Worker 0's card-close pass. Both are routed with owner `maintainer`; neither is in
any cohort's writable set, and no worker edits them here.

- **`docs/GLOSSARY.md`, the `DjangoListField` body - the same unqualified promise, consumer-facing.**
  Anchor identified by reading the rendered heading above the sentence, not by line number: the
  `## \`DjangoListField\`` heading (`docs/GLOSSARY.md:666`) owns the body, so the `GlossaryTerm`
  anchor is **`djangolistfield`**; the sentence is the last one of that body's
  **`**Row bound (\`0.0.14\`, spec-047).**`** paragraph (`docs/GLOSSARY.md:678` at this render).
  The spec's `## Doc updates` names the `DjangoListField` and execution-resource-policy bodies as
  Slice 5's to reconcile, so this is in scope for the card close rather than deferred. A
  flattened sweep of the whole render for the promise returns this one site (the
  `execution-resource-policy` body carries the bounds and their defaults but makes no slicing or
  `LIMIT` claim), so this is the complete glossary population, not a sample.

  **Exact old sentence**, as it reads in the current render:

  > The bound is applied by SLICING and only AFTER the [`get_queryset`](#get_queryset-visibility-hook) hook and any consumer-resolver post-processing, so a `QuerySet` carries it into SQL as a `LIMIT` / `OFFSET` while the hook still composes onto an unsliced source.

  **Exact replacement sentence:**

  > The bound is applied by SLICING and only AFTER the [`get_queryset`](#get_queryset-visibility-hook) hook and any consumer-resolver post-processing, so an unevaluated `QuerySet` carries it into SQL as a `LIMIT` / `OFFSET` while the hook still composes onto an unsliced source. A source whose rows are already fetched - a materialized sequence, a warm prefetch cache, or a queryset the consumer evaluated - is windowed in Python from the rows it holds instead, with no further query (`0.0.15`, spec-050).

  It is written free of apostrophes so it survives a `manage.py shell -c '<single-quoted>'` edit,
  but the safer route is the one this cycle already owes for the "Sealed execution queryset" body:
  a script in the scratchpad piped into `manage.py shell`, then `build_glossary_md.py`. A hand
  edit to the rendered file is reverted by the next render and goes red in CI's generator
  `--check`. This travels with the "Sealed execution queryset" replacement already recorded in
  `## Plan (Worker 1)` `### Notes for Worker 1 (spec reconciliation)` - one DB pass, two bodies,
  one regenerate.

- **`docs/SPECS/spec-047-resource_policy-0_0_14.md` - routed, owner `maintainer`, beside the two
  archived one-word fixes already routed** (`spec-045`'s and `spec-034`'s "unresolved" ->
  "malformed"). Its `**The bound is applied by SLICING**` bullet says "a `QuerySet` carries it
  into SQL as a `LIMIT` ... and is never evaluated unbounded", with the materialized case beside
  it. Amending a shipped spec is a round over that spec
  (`docs/builder/BUILD.md` `### Cohorting, naming, and closure`), never a slice edit, so it is
  recorded rather than touched. My reading, for the maintainer to accept or overturn: it describes
  `0.0.14`, where the evaluated-queryset case was an unstated corner rather than a documented
  contract, and the carry shipped after it - so unlike the two one-word fixes, whose sentences are
  made imprecise about behavior that still ships, this one is a dated record and plausibly needs
  nothing. It is written down so a later sweep rediscovering it finds a decision rather than a gap.

### Spec changes made (Worker 1 only)

Both edits are `## Definition of done` rows the carry falsified. A DoD row is graded literally, so
an unqualified row here would fail the shipped code: a grader checking "querysets retain SQL
`LIMIT/OFFSET`" against an evaluated source finds a `list` and no `LIMIT`. The four other homes
carrying the same vocabulary were examined and left unedited, with the reason recorded in
`### Low dispositions (pass 2)` item 3.

1. `docs/spec-050-list_field_arguments-0_0_15.md` `## Definition of done`, the "No raw-list row
   source decides its own ceiling" row (lines 2813-2818 as edited). "An exact `QuerySet` is sliced
   and keeps its SQL `LIMIT` ... so a sealable project queryset class keeps that `LIMIT`" is false
   for a source that arrives evaluated, which this cohort made a first-class documented case: the
   slice is then answered from the carried rows and returns a `list` with no `LIMIT` at all. Both
   halves now say `unevaluated`; the evaluated case is owned by the row four rows below, so
   nothing is duplicated. Triggered by the close cycle, Cohort A, pass 2.
2. Same file, `## Definition of done`, the "Querysets retain SQL `LIMIT/OFFSET`" row (lines
   2851-2854 as edited). Same falsehood, stated at the level of the whole seam; it now qualifies
   the retention to unevaluated querysets and names the evaluated behavior with a pointer to
   Decision 8 rather than restating it. Triggered by the close cycle, Cohort A, pass 2.

Gates over the edited paths: `uv run python scripts/check_spec_glossary.py --spec
docs/spec-050-list_field_arguments-0_0_15.md`; `uvx pre-commit run --files
docs/spec-050-list_field_arguments-0_0_15.md docs/builder/bld-050-close-row_carry.md`;
`uv run python scripts/check_citations.py --check`. Results recorded in the report to Worker 0.

## Build report (Worker 2, pass 4)

Scope: `### Low dispositions (pass 2)` item 1 only - the "keeps its type" clause in
`django_strawberry_framework/resource_policy.py::bounded_rows`'s docstring. Item 2 (routed) and
item 3 (a sweep, no edit owed) carry no builder work. No behavior, expectation or boundary
changes.

### Precondition

`git diff HEAD -- django_strawberry_framework/resource_policy.py` before any edit: two hunks, both
docstring-only - the pass-1 `_windowed_rows` "source that arrives evaluated" paragraph and the
pass-3 `bounded_rows` rewrite; 23 insertions / 15 deletions. Nothing else in the file.
`examples/fakeshop/db.sqlite3` md5 `2732e633f3303c55aac9d9f398e48df7` before and after every
command in this pass - identical, and the same value Worker 3 and Worker 1 recorded.

### Files touched

- `django_strawberry_framework/resource_policy.py` - the `bounded_rows` docstring's second
  paragraph. The dispatched replacement applied verbatim, plus the re-wrap it requires (below).
  Nothing else.

### The sentence written

The dispatched block landed word for word. Re-wrapped to the paragraph's own width, which the
dispatch permits and which this one needs twice over: the replaced span both starts and ends
mid-line in the original, and its old tail line carried a 46-column strand (`a bounded list of its
keys. A ``QuerySet```) left by pass 3's own mid-line dispatch. Applying the new text and stopping
there would have moved that strand to 16 columns, so the sentence the dispatch did not touch -
`A ``QuerySet`` subclass is the one shape ... ``ConfigurationError``.` - was reflowed with its
words untouched. Every line of the paragraph now sits at 65-80 columns; the file's one >99-column
line (121, 162 columns) is present identically at HEAD and was not touched.

Measured rather than read side by side, whitespace-flattened full text, WORK against
`git show HEAD:` in the scratchpad:

| Row | Count | Expected |
|---|---|---|
| dispatched replacement in WORK | 1 | 1 |
| dispatched replacement in HEAD | 0 | 0 |
| dispatched original in WORK | 0 | 0 |
| dispatched original in HEAD | 1 | 1 |
| the reflowed closing sentence, in its pre-pass wording, in WORK | 1 | 1 |
| control, needle in neither file | 0 | 0 |
| control, an untouched sentence of the same docstring | 2 (1 each) | 2 |

Row 5 is what makes the reflow auditable: the closing sentence is asserted at its pre-pass
wording, so a reflow that had silently reworded a word would count 0. The two controls establish
the counter can both miss and hit.

### Tests added or updated

None. A docstring pass adds no test.

### Validation run

- `uv run ruff format django_strawberry_framework/resource_policy.py` - **1 file left unchanged**.
- `uv run ruff check --fix django_strawberry_framework/resource_policy.py` - **All checks passed!**
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/resource_policy.py`
  - pass (ASCII-only holds; `text.isascii()` True independently).
- `uvx pre-commit run --files django_strawberry_framework/resource_policy.py` - all six hooks
  **Passed** on the first run; no hook rewrote the file.
- `uv run python scripts/check_citations.py --check` - **OK: 1108 citations resolve** (929 in 448
  `.py` files, 179 in `KANBAN.md`), the same figure as pass 3.
- `uv run pytest -n0 tests/test_resource_policy.py docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py --no-cov -q`
  - **293 passed** (288 + 5), exit 0, no `--cov*` flag.
- `git status --short` after both ruff invocations: `django_strawberry_framework/resource_policy.py`
  is the only slice-intended entry. The rest of the list is unchanged from Worker 3's and Worker
  1's: the concurrent session's `tests/mutations/*`, the two live example suites,
  `django_strawberry_framework/{permissions,schema,types/resolvers,utils/querysets}.py`,
  `docs/feedback.md`, `docs/TREE.md`, `docs/README.md`, `docs/bug_hunt/*`,
  `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`, the spec pair Worker 1 edited, and
  `examples/fakeshop/db.sqlite3`. **Stop-and-report, not a revert:** none touched, none reverted.
- Diff delta as a number: 23/15 insertions-deletions before this pass, **27/16 after** (+4/+1,
  net +3 lines). The new paragraph is 10 lines where 8 stood; the reflowed closing sentence is 6
  where 5 stood. That accounts for every line, so no earlier hunk was disturbed.

### Failability proofs

None; this pass introduced no new boundary. The inverse proof a docstring-only edit owes, run
against `git show HEAD:django_strawberry_framework/resource_policy.py` written to the scratchpad
(never a checkout - the tree is legitimately dirty with this cohort's own work):

| Row | Result | What it establishes |
|---|---|---|
| files byte-identical | False | an edit exists; the identity is not measuring an unmodified file |
| stripped-AST identical | **True**, `e3e820663f8e6d4f...` both | no executable line, constant, signature or default changed |
| un-stripped HEAD vs WORK | False | the stripper is what makes them equal; the identity is not vacuous |
| control, structural (`_CTRL_SENTINEL = 1` appended) | digest moves | the comparison can fail on a statement |
| control, string literal (`RESOURCE_LIMIT_EXCEEDED` rewritten) | digest moves | the stripper deletes docstrings only, not every string |
| control, inverse (`_attach_cleanup_note`'s docstring mutated - a docstring this diff never touches) | digest unchanged, bytes differ | the stripper really is deleting docstrings, so the True row means what it looks like |

The digest is the same `e3e8206...` Worker 3 and Worker 1 each derived independently at pass 3, so
the executable surface is unchanged from the version those two passes verified, not merely
unchanged from HEAD.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Owned by the final gate per the plan's declaration. A docstring carries no version-dependent
behavior.

### Implementation notes

- **Wrap width 78, not the dispatch's own ~70.** The blockquote's line breaks are an artifact of
  the artifact's own margin; the paragraph around it runs 78-82. Re-wrapping to the code's width
  is what the dispatch's "the words are the contract" asks for.
- **The reflow was safe to run only because no citer quotes these lines.** Pass 3 established zero
  `resource_policy.py #"..."` citations tree-wide; `check_citations.py --check` re-run here is the
  `::Symbol` half, and `bounded_rows` itself is neither renamed nor moved.

### Notes for Worker 3

- The diff carries two visible changes, one of them not dispatched: the replaced sentences, and a
  pure reflow of the following sentence. The reflow is asserted machine-to-machine in
  `### The sentence written` row 5 rather than left to a reader's eye - re-run that count rather
  than diffing the paragraph by hand, since a line-level diff shows the reflowed sentence as
  changed when its words are not.
- `docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py` is still the live oracle for
  the clause: its `test_evaluated_exact_queryset_is_windowed_in_python_with_no_query` asserting
  `type(rows) is list` for an exact `models.QuerySet` is exactly what the old "keeps its type"
  clause contradicted and the new "comes back as a ``list``" clause now states.

### Notes for Worker 1 (spec reconciliation)

None. The dispatch arrived with its replacement already written and the spec edits it implies were
made by Worker 1 in pass 2 (`### Spec changes made (Worker 1 only)`, both `## Definition of done`
rows). Nothing in this pass surfaced a gap, conflict or unstated assumption; no amendment is owed.

---

## Review (Worker 3, pass 4)

Scope: the pass-4 docstring edit in `django_strawberry_framework/resource_policy.py::bounded_rows`
only - the dispatched "keeps its type" replacement from `### Low dispositions (pass 2)` item 1, plus
the word-preserving reflow of the sentence that follows it. Everything earlier in this cohort was
accepted at passes 1 and 3 and re-verified at Worker 1's pass 2; nothing in this diff touches it.
`examples/fakeshop/db.sqlite3` md5 `2732e633f3303c55aac9d9f398e48df7` before and after every command
in this pass - identical, and the same value passes 3 and 4 recorded.

### The dispatched block, compared machine-to-machine

Both blockquotes were cut out of this artifact by line span (original 2982-2989, replacement
2993-3003), un-quoted, whitespace-flattened, and counted against the flattened working file and
against `git show HEAD:django_strawberry_framework/resource_policy.py` written to the scratchpad
(never a checkout). The reflowed following sentence is asserted at its **pre-pass** wording, cut
from pass 3's own dispatch blockquote (artifact lines 2359-2364), so a reflow that reworded a single
word counts 0.

| Row | WORK | HEAD | Expected |
|---|---|---|---|
| dispatched replacement (pass 4) | 1 | 0 | 1 / 0 |
| dispatched original (pass 4) | 0 | 1 | 0 / 1 |
| the reflowed closing sentence, at its pre-pass wording | 1 | 0 | 1 / 0 |
| control HIT: pass-3's opening replacement, untouched this pass | 1 | 0 | 1 / 0 |
| control MISS: a needle in neither file | 0 | 0 | 0 / 0 |
| control HIT both: a sentence untouched since HEAD | 1 | 1 | 1 / 1 |

Line-for-line comparison is the wrong instrument here and would report drift where there is none:
the replaced span both starts and ends mid-line. Flatten first, then conclude.

### The whole file reconstructed from HEAD plus the recorded edits

Row 3 above proves the one sentence Worker 2 named. It cannot see a word changed anywhere else in
the file, so the stronger instrument was run as well: start from flattened HEAD, apply the cohort's
**four** recorded edits as string substitutions - the pass-1 `_windowed_rows` paragraph (insertion),
pass-3's two dispatched sentences, pass-4's dispatched clause - each asserted to match exactly once
before it is applied, and compare the result to the flattened working file.

**Equal.** So the working file's text is HEAD plus exactly those four edits and nothing else: no
fifth sentence, no reworded word inside the reflow, and - because flattening keeps every token,
including ones no AST carries - **no comment change either**. That closes the blind spot a
stripped-AST identity has by construction.

### The clause against the code, measured

- `uv run pytest -n0 docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py tests/test_resource_policy.py --no-cov -q`
  - **293 passed**, exit 0, **0** collection or setup errors, no `--cov*` flag.
- The pass-3 oracle pins only the queryset arms. The sentence pass 4 wrote is wider than that - "The
  slice answers in the sliced value's own type, except on a queryset whose rows are already fetched"
  quantifies over the whole enumeration - so a second oracle was written for the half nothing graded:
  `docs/builder/temp-tests/050/row_carry/test_w3_pass4_own_type.py`, **9 passed**. Exact `list`,
  `tuple`, `str`, `bytes` and `bytearray` each come back as their own type at the policy bound; an
  unevaluated exact queryset comes back as a `QuerySet`; an evaluated one comes back as a `list`
  (the sentence's sole exception); a `list` **subclass** comes back as a plain `list`, which is the
  negative control proving the type assertion can fail; and a last row asserts the enumeration is the
  code's own closed set - `set(_SLICE_BOUNDED_ROW_TYPES) == {list, tuple, str, bytes, bytearray,
  QuerySet}` - so the sentence enumerates a population rather than sampling one.
- The mechanism clause is true of the installed Django, read rather than assumed:
  `django/db/models/query.py::QuerySet.__getitem__` answers `return self._result_cache[k]` before it
  reaches `_chain()` whenever the cache is populated, so a slice of an evaluated queryset is a list
  slice and the returned type is `list`.
- `bounded_rows_async` owes no edit, confirmed independently of pass 3's finding: its docstring says
  "**lazy** querysets retain their SQL ``LIMIT``", which is scoped to the unevaluated state and makes
  no claim about an evaluated one.

### The diff is docstring-only, proved two ways

Stripped-AST identity against `git show HEAD:` in the scratchpad, docstrings removed from module,
class and function bodies:

| Row | Result | What it establishes |
|---|---|---|
| files byte-identical | False | an edit exists; the identity is not measuring an unmodified file |
| stripped-AST identical | **True**, `e3e820663f8e6d4f...` both | no executable line, constant, signature or default changed |
| un-stripped HEAD vs WORK | False | the stripper is what makes them equal; the identity is not vacuous |
| control, structural (`_CTRL_SENTINEL = 1` appended) | digest moves | the comparison can fail on a statement |
| control, string literal (`"RESOURCE_LIMIT_EXCEEDED"` rewritten) | digest moves | the stripper deletes docstrings only, not every string |
| control, inverse (`_raw_list_bound`'s docstring mutated - byte-identical at HEAD, touched by no hunk of this cohort) | digest unchanged, bytes differ | the stripper really is deleting docstrings, so the True row means what it looks like |

The digest is the same `e3e8206...` Worker 3 and Worker 1 derived at pass 3 and Worker 2 re-derived
here, so the executable surface is unchanged from the version those passes verified, not merely from
HEAD. The second proof is the reconstruction above, which covers what AST identity cannot see.

`git diff --numstat HEAD` on the file: **27 / 16**, the figure the build report states.

### No process provenance, and the surrounding conventions

- The 27 added lines were scanned flattened and case-folded for pass / slice / worker / card /
  spec-number / severity / review-doc / "previously" / "as of 0.0.N" / `TODO(` vocabulary: **0 hits**,
  with a positive control (`queryset`, 8 hits) proving the counter reads the text.
- `text.isascii()` **True** independently of the hook.
- Every line of the rewritten paragraph sits at 27-81 columns. The file's one over-length line
  (line 121, 162 columns) is present identically at HEAD and was not touched.
- Citation surface: a tree-wide sweep for `resource_policy.py ... #"..."` over 747 tracked files
  returns two hits, both naming `extensions/resource_policy.py` (a different path, in
  `docs/SPECS/spec-047-*` and `docs/builder/DONE/build-047-*`), neither quoting text in this file.
  So the reflow, which moves line breaks inside a sentence, strands no `#"substring"` citer.
- Retired-phrase census, flattened and case-folded over 744 readable tracked files: `keeps its type`
  survives in exactly two places, both true as written - `docs/spec-050-list_field_arguments-0_0_15.md`
  Decision 8's "an exact built-in sequence receives the same slice and **keeps its type**", whose
  subject excludes the queryset (my own oracle pins it), and `tests/filters/test_inputs.py`, about a
  `relay.GlobalID`. `keeps its own type` and `retains its type`: 0. The partial-claim residual this
  dispatch existed to close is closed.

### High:

None.

### Medium:

None.

### Low:

#### The sentence's two type promises are pinned only by gitignored temp tests

`bounded_rows` is in `resource_policy.py`'s `__all__`, and this pass is what makes the returned type
an explicit statement of its public contract ("answers in the sliced value's own type ... the window
comes back as a ``list``"). Nothing in the permanent suite asserts either half. The evaluated rows -
`tests/test_resource_policy.py:2211` and `:2229` - assert the rows and `django_assert_num_queries(0)`
but not `type(rows) is list`; `test_bounded_rows_slices_a_sequence_to_the_policy_bound`
(`tests/test_resource_policy.py:956`) asserts `== [0, 1]`, which a list-subclass-returning
implementation would also satisfy (a tuple would not: `(0, 1) == [0, 1]` is False). The only oracles for the sentence are
`docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py` and this pass's
`test_w3_pass4_own_type.py`, both gitignored and both inside `clean_up.py`'s deletion glob - so the
day this cycle closes, the new public promise has no pin at all. `worker-3.md` "Temp test rules" is
explicit that a temp test must not remain the only proof of shipped behavior.

**Not a blocker and not remediated here.** Nothing is false today, the behavior is unchanged by this
pass, and Worker 2's writable set for pass 4 was this one docstring "and nothing else in the file" -
adding permanent assertions is a different pass's work. Routed to Worker 1 below with the exact
one-line additions.

#### A 65-column strand mid-paragraph at the pass-3 edit boundary

Line 1062 (`the response from serializing them and costs no second query.`) ends a sentence at 65
columns and the next sentence starts on line 1063, inside the same paragraph. **Rejected, not a
finding for this pass:** the strand is the boundary of pass 3's dispatch, was present in the state
pass 3 accepted, renders as one paragraph either way, and re-wrapping it would be an undispatched
edit to text this dispatch did not name. Worker 2's reflow of the *following* sentence was owed
because that one's strand was a 46-column tail the new text would have cut to 16.

### DRY findings

None to act on. One examined and rejected: the evaluated-source mechanism is now stated in two
docstrings - `_windowed_rows`' pass-1 paragraph ("``QuerySet.__getitem__`` reads a populated
``_result_cache`` directly ... costs no query") and `bounded_rows`' new clause ("answers from the
rows it holds, so the window comes back as a ``list``"). They are not one definition written twice:
each documents its own surface, they state different consequences of the same mechanism (query cost
versus returned type), and `_windowed_rows` is package-private, so a reader of the exported helper
cannot be sent to it. `docs/dry/DRY.md` counts authoritative definitions, not projections; the
authoritative definition is the code, and neither docstring is a copy of the other. No abstraction
was added, so there is no existence challenge to raise.

### Failability audit

The diff introduces no boundary, guard, gate or rejection path - proved, not asserted, by the
stripped-AST identity above, which makes the executable surface bit-identical to HEAD. Worker 2's
`None; this pass introduced no new boundary.` is correct, the re-run floor is therefore empty
legally, and the inverse proof a docstring-only edit owes instead was re-run independently (table
above) with all four controls, plus the reconstruction that covers comments.

### Hot-path budget

Not applicable; plan declares no hot path, and no executable line changed.

### Floor verification

Owned by the final gate per the plan's declaration. A docstring carries no version-dependent
behavior; the AST identity is the proof of that here rather than a claim.

### Test staleness sweep, run independently of the diff's file list

Swept the whole tree rather than the artifact's `### Files touched`: `__doc__` appears 10 times in
first-party `.py` files, and the only occurrences under `tests/` or `examples/` are two dict keys
constructing types in `examples/fakeshop/test_query/test_resource_policy_api.py` - nothing reads
`bounded_rows.__doc__`. No doctest configuration exists (`doctest` appears in no `.py`, `pytest.ini`
or `pyproject.toml`). The six files naming `bounded_rows` under `tests/` and `examples/` were listed
and none asserts on docstring text. A docstring edit cannot stale a row in any of the four trees.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export
list are unchanged. `resource_policy.py`'s own `__all__` is inside the AST-identity proof, so it too
is unchanged.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The spec pair dirty in the
tree is Worker 1's pass-2 edit, not this pass's, and the glossary and archived-spec homes are routed
to the maintainer under Worker 1's pass-2 notes.

### Gates

- `uvx pre-commit run --files django_strawberry_framework/resource_policy.py` - all six hooks
  **Passed** on the first run; no hook rewrote the file.
- `uv run python scripts/check_citations.py --check` - **OK: 1108 citations resolve** (929 in 448
  `.py` files, 179 in `KANBAN.md`), unchanged from passes 3 and 4.
- `git status --short` after every command: identical to the population Worker 2 and Worker 1
  recorded - the concurrent session's `tests/mutations/*`, the two live example suites, the four
  other package modules, `docs/feedback.md`, `docs/TREE.md`, `docs/README.md`, `docs/bug_hunt/*`,
  `docs/builder/DONE/build-050-*`, the spec pair, and the tracked DB. **Stop-and-report, not a
  revert:** none touched, none reverted.

### Spec slice checklist

Both boxes remain `- [x]` and remain true: a docstring pass moves no contract, and the clause-by-
clause tick warrant Worker 1 wrote at final verification is unaffected by a change with an identical
stripped AST. Nothing to un-tick, nothing deferred.

### What looks solid

- The dispatch landed word for word and the reflow really is word-preserving - and both facts are
  measured at the file level, not the sentence level, so the acceptance does not rest on a reader
  having looked in the right place.
- Worker 2 named the undispatched half of its own diff (the reflow) in `### Notes for Worker 3` and
  supplied the instrument for checking it rather than leaving a reviewer to diff by eye. That is the
  disclosure that makes a reflow reviewable at all.
- The new sentence is narrower and truer than what it replaced: it states the type rule once, names
  its single exception, and gives the exception's mechanism (`QuerySet.__getitem__` answering from
  held rows), which is checkable against Django rather than against the package's intent.
- The "except" is scoped to the queryset, so the built-in-sequence half of the enumeration stays
  true - the obvious over-correction (qualifying the whole enumeration) was avoided.

### Temp test verification

- `docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py` - re-run by me, 5 passed;
  still the live oracle for the queryset arms.
- `docs/builder/temp-tests/050/row_carry/test_w3_pass4_own_type.py` - **written this pass**, 9
  passed; covers the built-in-sequence half of the new sentence and the closed-set enumeration, with
  a negative control (a `list` subclass) proving the type assertion can fail.
- Disposition: both **kept for the cycle, neither promoted by this pass** - neither caught a defect,
  and promoting is outside a docstring pass's writable set. The consequence of leaving them as the
  only oracles is the Low above, routed to Worker 1 rather than left implicit.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low): pin the public return-type promise, or record that it needs no pin.** The
  sentence this pass shipped states `bounded_rows`' returned type as a public contract; the permanent
  suite pins neither half. Two resolution paths - (a) at card close, add `assert type(rows) is list`
  to `tests/test_resource_policy.py:2211` and `:2229` (the two evaluated rows, which already hold the
  source and the zero-query assertion, so the addition is one line each and needs no new fixture) and
  one row asserting an exact `tuple`/`str`/`bytes`/`bytearray` comes back as its own type; or (b)
  record the decision that Python's slice semantics on an exact built-in need no pin and the
  evaluated-queryset arm is adequately pinned by its row-identity assertions. Either is defensible;
  what is not is closing the cycle with `clean_up.py` deleting the only two oracles. Worker 3 raises,
  Worker 1 or the maintainer decides.
- No spec gap surfaced by this pass. The two `## Definition of done` rows Worker 1 amended at pass 2
  are consistent with the docstring as it now reads, and Decision 8's own "an exact built-in sequence
  ... keeps its type" clause is true because its subject excludes the queryset - checked, not assumed.

### Review outcome

`review-accepted`. The dispatched block landed verbatim, the reflow preserves every word, the whole
file is HEAD plus exactly the cohort's four recorded edits, the clause is true in every arm the
sentence quantifies over, the diff is docstring-only under two independent proofs, and every gate is
green. One Low is escalated to Worker 1 with its resolution paths; one Low is recorded with its
rejection reason. Neither blocks acceptance.

---

## Final verification (Worker 1, pass 3)

Scope: the pass-4 docstring edit only, plus the one Low Worker 3 escalated. The carry, the
admission and the whole executable surface were verified at pass 1 and re-verified at pass 2;
nothing in this diff touches them.

- **The dispatched block landed verbatim**, re-measured here rather than read against Worker 2's
  and Worker 3's tables. Both blockquotes were cut out of this artifact by line span (original
  2982-2989, replacement 2993-3003), un-quoted, whitespace-flattened, and counted against the
  flattened working file and against `git show HEAD:django_strawberry_framework/resource_policy.py`
  written to `<scratch>/w1p3/rp.HEAD.py` (never a checkout). The reflowed following sentence is
  asserted at its **pre-pass** wording, cut from pass 3's own dispatch blockquote (artifact lines
  2359-2364), so a reflow that reworded one word counts 0.

  | Row | WORK | HEAD | Expected |
  |---|---|---|---|
  | pass-4 dispatched replacement | 1 | 0 | 1 / 0 |
  | pass-4 dispatched original | 0 | 1 | 0 / 1 |
  | the reflowed closing sentence, at its pre-pass wording | 1 | 0 | 1 / 0 |
  | control HIT: pass-3's opening replacement, untouched this pass | 1 | 0 | 1 / 0 |
  | control MISS: a needle in neither file | 0 | 0 | 0 / 0 |
  | control HIT both: an untouched module-docstring sentence | 1 | 1 | 1 / 1 |

- **The diff is docstring-only**, by stripped-AST identity against the same scratchpad copy of
  `git show HEAD:`, with four controls:

  | Row | Result | What it establishes |
  |---|---|---|
  | files byte-identical | False | an edit exists; the identity is not measuring an unmodified file |
  | stripped-AST identical | **True**, `e3e820663f8e6d4f...` both | no executable line, constant, signature or default changed |
  | un-stripped HEAD vs WORK | False | the stripper is what makes them equal; the identity is not vacuous |
  | control, structural (`_CTRL_SENTINEL = 1` appended) | digest moves | the comparison can fail on a statement |
  | control, string literal (`RESOURCE_LIMIT_EXCEEDED` rewritten) | digest moves | the stripper deletes docstrings only, not every string |
  | control, inverse (a module-docstring sentence no hunk of this cohort touches, mutated) | digest unchanged, bytes differ | the stripper really is deleting docstrings, so the True row means what it looks like |

  The digest is the same `e3e8206...` that passes 3 and 4 derived, so the executable surface is
  unchanged from the version those passes verified, not merely from HEAD.

  **The comment blind spot closed with its own instrument.** A stripped AST cannot see a comment by
  construction, so the `tokenize` COMMENT token sequences of HEAD and WORK were compared directly:
  **85 tokens each, sequences identical**, with a control (one comment mutated) proving the
  comparator can report a difference. Executable surface identical and comment stream identical
  means the 27/16 diff is docstring text and nothing else - proved two ways rather than inferred
  from a diff read by eye. (Worker 3's HEAD-plus-four-recorded-edits reconstruction reaches the same
  conclusion from the other direction; this is an independent instrument, not a restatement.)

- **Gates.** `uvx pre-commit run --files django_strawberry_framework/resource_policy.py` - all six
  hooks **Passed** on the first run, no re-run needed.
  `uv run python scripts/check_citations.py --check` - **OK: 1108 citations resolve** (929 in 448
  `.py` files, 179 in `KANBAN.md`), unchanged from passes 2, 3 and 4.
  `uv run pytest -n0 tests/test_resource_policy.py --no-cov -q` - **288 passed**, exit 0, no
  `--cov*` flag.

- **Spec slice checklist:** both boxes remain `- [x]` and remain true. The clause-by-clause tick
  warrant in `### Spec slice checklist (verbatim)` is unaffected by a change whose stripped AST and
  comment stream are both identical to the state that warrant was written against. Nothing
  deferred, nothing over-ticked.

- **Concurrent work, stop-and-report.** `examples/fakeshop/db.sqlite3` md5
  `2732e633f3303c55aac9d9f398e48df7` before and after every command in this pass - the same value
  passes 2, 3 and 4 recorded. The historical snapshot's `HEAD` was `20646db2`, the same commit
  pass 2 measured against.
  `git status --short` is the population the last three passes recorded: the concurrent session's
  `tests/mutations/*`, `django_strawberry_framework/schema.py` (which the DONE record's partition
  folds into Cohort B), the three live example suites it
  owns, `docs/feedback.md`, `docs/TREE.md`, `docs/README.md`,
  `examples/fakeshop/test_query/README.md`, `docs/bug_hunt/*`,
  `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`, plus this cohort's own files and
  the spec pair. None touched, none reverted.

- **Final status:** `revision-needed`. One assertion per row in four existing rows closes the last
  open item; everything else in the cohort is accepted.

### Low disposition (pass 3): the pin is OWED

**Worker 3's escalated Low, decided: `revision-needed`, one builder pass, four lines.**

The pass-4 sentence makes `bounded_rows`' returned type an explicit statement of a public contract
(`bounded_rows` is in `resource_policy.py`'s `__all__`). Two facts decide it.

1. **The suite already treats that returned type as pinned - on the other arm.** Five permanent
   rows assert `type(rows) is QuerySet` through these same two helpers (the `:2025` row uses
   `_windowed_rows`) on an UNEVALUATED source
   (`tests/test_resource_policy.py:2001`, `:2013`, `:2025`, `:2061`, `:2081`). The evaluated arm is
   the one this cohort created, is the sentence's sole named exception, and is pinned by nothing.
   That asymmetry is the finding: the contract is not "too obvious to pin" here, because the
   package pins it one state over.
2. **The evaluated arm's type is package behavior, not language semantics.** It holds only because
   the seal carries `_result_cache` onto the rebuild and `QuerySet.__getitem__` then answers from
   held rows. An implementation that re-queried, or that returned a lazily sliced queryset, would
   still satisfy every assertion those four rows make today: `assert list(rows) == held[:2]` wraps
   the result in `list()` and `assert [row is held[index] ...]` iterates it, so both are
   type-agnostic, and `django_assert_num_queries(0)` cannot see a slice that has not been evaluated
   yet. The rows are correct and load-bearing for what they pin; they simply do not reach the type.

The oracles that do reach it - `docs/builder/temp-tests/050/row_carry/test_w3_pass3_docstring.py`
and `test_w3_pass4_own_type.py` - are gitignored and inside `clean_up.py`'s deletion glob, so on
the day this cycle closes the promise would have no pin at all.

**Measured before dispatching, not assumed.** A throwaway probe in the session scratchpad
(`<scratch>/w1p3/test_w1p3_probe.py`, run as
`uv run pytest -c pytest.ini -n0 <scratch>/w1p3/test_w1p3_probe.py --no-cov -q`) - **6 passed**:
`type(rows) is list` holds for an exact queryset and for a no-override subclass, through
`bounded_rows` and through `bounded_rows_async`, plus the coordinate window; and a negative control
asserts an unevaluated source comes back `QuerySet` and not `list`, so the assertion being
dispatched can fail. The probe is scratch and is not promoted - the four permanent rows below are.

#### Exact assertions to add (Worker 2)

In `tests/test_resource_policy.py`, four rows, one line each, and nothing else in the file. In each
one insert

```python
    assert type(rows) is list
```

as the line **immediately preceding that row's `assert list(rows) == held[:2]`** (the target line is
byte-identical in all four rows, which is what makes the placement unambiguous). Leave every
existing assertion byte-identical - in particular do not rewrite `list(rows)` to `rows`, which would
change what the equality proves.

The four node ids:

- `tests/test_resource_policy.py::test_an_evaluated_exact_queryset_is_windowed_from_the_rows_it_holds` (sync, exact; line 2211)
- `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds` (sync, subclass; line 2229 - the new line sits after `assert materialized_rows(rebuilt) is held`)
- `tests/test_resource_policy.py::test_an_evaluated_exact_queryset_is_windowed_from_its_own_rows_when_awaited` (async, exact; line 2276)
- `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited` (async, subclass; line 2298)

Line numbers are pin-at-write-time hints; the node ids and the anchor assertion are the contract.

**No new fixture, no new row, no docstring rewrite is owed.** Each of the four already seeds, builds
its evaluated source, holds `held`, and names `rows`. If a docstring clause is added anyway it
states the invariant in one plain clause (the window is answered from the rows the source holds, so
it is a `list`) and never the history of this pass.

**No failability proof is owed and no control row is owed.** The pass adds no boundary, guard or
rejection path, so `### Failability proofs` is `None; this pass introduced no new boundary.` The
assertion is not vacuous by construction: `test_an_exact_queryset_still_carries_the_row_bound_into_sql`
(`tests/test_resource_policy.py:2061`) asserts `type(rows) is QuerySet` through the same helper on an
unevaluated source of the same class, so the permanent suite already carries the contrasting verdict.
Record in the build report that this row was read and names the opposite type.

**Two things explicitly NOT dispatched, with the reason each is not owed:**

- **The built-in half of the sentence** ("The slice answers in the sliced value's own type") for
  `tuple`, `str`, `bytes`, `bytearray`. Worker 3 offered it as part of path (a); it is declined. That
  clause is CPython slice semantics on exact built-ins, so a row asserting it pins the interpreter
  rather than this package; the package's own contribution at that seam is the slice-versus-count
  DISPATCH (`_SLICE_BOUNDED_ROW_TYPES`, `_bounds_by_its_own_slice`), which is already pinned by the
  subclass, mapping and bare-iterable rows, and the `list` member is pinned by
  `test_bounded_rows_slices_a_sequence_to_the_policy_bound`'s `== [0, 1]` (a tuple return fails it).
  The clause also pre-exists this cohort at HEAD; only the `except on a queryset ...` exception is
  new, and that is what the four rows pin.
- **`test_a_coordinate_window_over_an_evaluated_project_queryset_class_reads_carried_rows`**
  (line 2255). The sentence under repair is `bounded_rows`' docstring; `_windowed_rows` is
  package-private and its own pass-1 paragraph makes a query-cost claim, not a type claim. The probe
  shows the assertion would pass there; it is not required, and adding it is not a defect either.

### Deferred and routed items: every one has a named owner

Confirmed by re-reading the artifact's routing sections and re-checking each target on disk at this
HEAD. Nothing is deferred without an owner, and no routed replacement text has gone stale.

| Item | Owner | Still live and unedited in the historical snapshot (`20646db2`) |
|---|---|---|
| `docs/GLOSSARY.md` "Sealed execution queryset" body - `_result_cache` "never copied forward" | `maintainer`, Worker 0's card-close DB pass | quoted old text occurs **1**, replacement **0** (discharged in substance since) |
| `docs/GLOSSARY.md` `DjangoListField` body - the unqualified `LIMIT` / `OFFSET` promise | `maintainer`, same DB pass | quoted old sentence occurs **1**, replacement **0** (discharged since) |
| `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` "unresolved" -> "malformed" | `maintainer` | **1** hit |
| `docs/SPECS/spec-034-permissions-0_0_10.md` "unresolved" -> "malformed" | `maintainer` | **1** hit |
| `docs/SPECS/spec-047-resource_policy-0_0_14.md` `**The bound is applied by SLICING**` bullet | `maintainer` (recorded reading: a dated `0.0.14` record, plausibly needs nothing; amended by `b3458ee8` with the evaluated-source case) | **1** hit |
| Robustness row - an exact `QuerySet` carrying a foreign `_result_cache` bypasses the ceiling | `maintainer`, the DONE record's catalog, not `BACKLOG.md` (`AGENTS.md` rule 35: condition (c) fails outright) | pre-existing at HEAD, unchanged |
| `_UNRECOMPOSED_CHILD_POLICY` has no production reader after `fd39cac6` | `maintainer` (delete-or-correct, file in no cohort's set) | unchanged (retired by `4d9f1c3d`) |
| Decision 20's connection-field separation | `maintainer` until a card number exists, on a new card | recorded in the rationale (discharged by `fee87ac4`/`c87f4f98`, card 053) |

Both glossary replacements were re-matched against the CURRENT render with whitespace flattened
rather than trusted from the earlier pass: each old text occurs exactly once and neither replacement
is present, so both are still a paste and not a rewrite.

### Summary

The cohort ships the evaluation-state carry at the raw-list seam and the sealer admission that made
it reachable for a project queryset class, with the docstrings on `bounded_rows`, `_windowed_rows`,
`normalized_row_source`, `materialized_rows` and `_prepared_visibility_source` corrected to the
shipped behavior. Pass 4 closed the last false clause in `bounded_rows`' public docstring. What
remains open is not a falsehood but an unpinned one: the returned type that clause now promises for
an evaluated source has no permanent oracle, and four one-line assertions close it.

### Spec changes made (Worker 1 only)

None this pass. No behavior, expectation or boundary changed, the stripped AST and the comment
stream are both identical to HEAD, and the two `## Definition of done` rows amended at pass 2 remain
accurate. Decision 8's "an exact built-in sequence receives the same slice and keeps its type" was
re-read against the pass-4 docstring: its subject excludes the queryset, so it is true as written and
needs no edit. No spec home is falsified by the pin decision - no home in the spec or the rationale
claims the evaluated returned type at all.

---

## Build report (Worker 2, pass 5)

Scope: the four one-line assertions dispatched by `### Low disposition (pass 3): the pin is OWED`,
and nothing else in the file.

### Files touched

- `tests/test_resource_policy.py` - four lines inserted, one per evaluated-source row, each the
  line immediately preceding that row's `assert list(rows) == held[:2]`. No other edit: no
  docstring rewrite, no new fixture, no new row, and every existing assertion is byte-identical
  (in particular `list(rows)` was not rewritten to `rows`).

The insertion was made by anchor, not by line number. The file was read, the anchor line
`    assert list(rows) == held[:2]` was asserted to occur **exactly 4 times** before anything was
written, and the four hits were confirmed to be the four dispatched node ids (2224, 2250, 2293,
2308 at pin time). The coordinate-window row is not in the population - its anchor is
`held[1:3]` - so the "explicitly NOT dispatched" row could not be hit by accident. A partial
match would have aborted with nothing written.

### Tests added or updated

- `tests/test_resource_policy.py::test_an_evaluated_exact_queryset_is_windowed_from_the_rows_it_holds`
  - the window over an evaluated exact `QuerySet` returns an exact `list`.
- `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds`
  - same, through the rebuild of a project queryset class (the new line sits after
  `assert materialized_rows(rebuilt) is held`).
- `tests/test_resource_policy.py::test_an_evaluated_exact_queryset_is_windowed_from_its_own_rows_when_awaited`
  - same on the awaited seam, exact source.
- `tests/test_resource_policy.py::test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited`
  - same on the awaited seam, project queryset class.

New line numbers after formatting: 2224, 2251, 2295, 2311.

### Validation run

- `uv run ruff format tests/test_resource_policy.py` - **1 file left unchanged** (the inserted
  lines are already formatter-stable; the usual `COM812`-conflict warning is the standing one).
- `uv run ruff check --fix tests/test_resource_policy.py` - **All checks passed!**
- `uv run python scripts/check_trailing_commas.py --check tests/test_resource_policy.py` - clean,
  exit 0, no output.
- `uvx pre-commit run --files tests/test_resource_policy.py` - all six hooks **Passed** on the
  first run, no rewrite, no re-stage.
- `uv run pytest -n0 tests/test_resource_policy.py --no-cov -q` - **288 passed**, exit 0. Same 288
  the last three passes recorded: this pass adds assertions to existing rows, not rows, so the
  collected count is expected to be unchanged and is.
- The four node ids alone,
  `uv run pytest -c pytest.ini -n0 --no-cov -q -p no:cacheprovider <the four ids>` - **4 passed**,
  4 collected. Running them as their own selection is what shows the four ids are real and
  spelled correctly; a typo would have been an empty selection, not a failure.
- `git status --short` after both ruff invocations - the population the last three passes
  recorded, unchanged: the concurrent session's `tests/mutations/*`,
  `django_strawberry_framework/{permissions,resource_policy,schema,types/resolvers,utils/querysets}.py`,
  the live example suites, `docs/{README,TREE,feedback}.md`,
  `examples/fakeshop/test_query/README.md`, `docs/bug_hunt/*`,
  `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`, the spec pair, plus this cohort's
  own files. **No new path appeared.** Nothing touched, nothing reverted.
- `examples/fakeshop/db.sqlite3` md5 `2732e633f3303c55aac9d9f398e48df7` before and after every
  command in this pass - the same value passes 2, 3, 4 and Worker 1's pass 3 recorded. The
  historical snapshot's `HEAD` was `20646db2`.

**The diff delta is the precondition, measured both sides.** `git diff HEAD --stat --
tests/test_resource_policy.py` read **204 insertions, 5 deletions** before the edit - the
pass-1/pass-2 hunks and nothing else - and **208 insertions, 5 deletions** after. Exactly four
lines added, zero removed, zero existing lines rewritten. A diffstat taken only after the edit
could not distinguish four new lines from four rewritten ones; the deletion count staying at 5 is
what does.

### Failability proofs

None; this pass introduced no new boundary.

The assertion is nonetheless not vacuous, on two independent warrants, neither of which is this
pass's own work:

- **The permanent suite already carries the contrasting verdict.**
  `tests/test_resource_policy.py::test_an_exact_queryset_still_carries_the_row_bound_into_sql`
  (line 2054, assertion at 2061) was read end to end this pass: it calls the same `bounded_rows`
  on an UNEVALUATED exact `QuerySet` of the same class and asserts `type(rows) is QuerySet`, then
  `rows.query.high_mark == 2`. Four more rows do the same at 2001, 2013, 2025 and 2081. So a
  `bounded_rows` that returned `list` unconditionally fails five permanent rows, and one that
  returned `QuerySet` unconditionally fails the four added here. Neither type can satisfy both
  arms - that is what makes each side an assertion rather than a tautology.
- **The negative control already exists and was re-run rather than re-invented.** Worker 1's
  pass-3 probe, `<scratch>/w1p3/test_w1p3_probe.py`, carries
  `test_negative_control_unevaluated_is_not_a_list`, which asserts an unevaluated source comes
  back `QuerySet` and `is not list`. Re-run at this working tree as
  `uv run pytest -c pytest.ini -n0 --no-cov -q -p no:cacheprovider <scratch>/w1p3/test_w1p3_probe.py`
  - **6 passed**, unchanged from the 6 Worker 1 measured. The probe is scratch, is not promoted,
  and is not this pass's evidence of the pin; it is the evidence that the dispatched assertion
  discriminates.

No transient mutation was applied to the package. A mutation that made the carry return
`tuple(...)` would have measured the same thing the contrasting rows already measure, at the cost
of editing a file outside this pass's writable set.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Owned by the final gate per the plan's declaration.

### Implementation notes

- **Inserted above the equality, not below it**, exactly as dispatched. A type assertion placed
  after `assert list(rows) == held[:2]` would report the equality's failure first on a regression
  that changed the type, which is the less specific diagnosis of the two.
- **`type(rows) is list`, never `isinstance`.** The contract is the exact type - the same spelling
  the five `type(rows) is QuerySet` rows on the unevaluated arm use, and the same spelling the
  seal's own refusal of a non-`list` cache turns on. `isinstance` would admit a `list` subclass and
  pin nothing the sentence promises.
- **No docstring clause added.** The disposition permits one and does not owe one; four rows whose
  docstrings already say the window is answered from the rows the source holds do not read more
  clearly for a restatement of the same invariant in a fifth place.

### Notes for Worker 3

- The diff to review is four lines. `git diff -- tests/test_resource_policy.py` also shows the
  pass-1/pass-2 hunks, which are already `review-accepted`; the four `+    assert type(rows) is
  list` lines are the whole of pass 5.
- The re-run negative control lives outside the repo, in the session scratchpad at
  `<scratch>/w1p3/test_w1p3_probe.py`. It is Worker 1's file, unedited by this pass.
- The one row the disposition explicitly declined,
  `test_a_coordinate_window_over_an_evaluated_project_queryset_class_reads_carried_rows`, is
  unchanged and still has no type assertion. That is intended, not an omission.

### Notes for Worker 1 (spec reconciliation)

None. The pass adds assertions to four existing rows; it changes no behavior, no boundary and no
expectation, and no spec home claims the evaluated returned type. The `### Spec slice checklist
(verbatim)` boxes are both already `- [x]` and remain true - this pass lands no new contract, so
nothing was newly ticked and nothing is over-ticked.

---

## Review (Worker 3, pass 5)

Scope: the four one-line assertions dispatched by `### Low disposition (pass 3): the pin is OWED`.
Everything else in the cohort is already `review-accepted` at passes 3 and 4 and was re-measured
only where a delta could hide (the file-level reconstruction below).

### High:

None.

### Medium:

None.

### Low:

None.

### The delta is exactly the four lines, measured by reconstruction rather than read

The working file was copied to `<scratch>/w3p5/trp.WORK.py`, the four occurrences of the exact
line `    assert type(rows) is list` were located and removed, and the result
(`<scratch>/w3p5/trp.PRIOR.py`) was diffed against `git show HEAD:tests/test_resource_policy.py`:
**204 insertions, 5 deletions**, the pass-1/pass-2 diffstat the prior review was written against.
A diffstat taken only on the current tree (208/5) cannot distinguish four added lines from four
added plus one rewritten elsewhere; subtracting the four and landing back on 204/5 can, because any
other edit would move that number.

| Measurement | Result |
|---|---|
| exact-match occurrences of the inserted line in WORK | **4**, at 2224, 2251, 2295, 2311 |
| occurrences at HEAD | 0 |
| occurrences of the anchor `    assert list(rows) == held[:2]` in WORK | **4**, at 2225, 2252, 2296, 2312 |
| every insert immediately precedes an anchor | **True** |
| anchors with no insert above them | **0** (4 anchors, 4 inserts) |
| WORK-minus-four-lines vs HEAD | **204 insertions, 5 deletions** |
| `git diff HEAD --stat -- django_strawberry_framework/resource_policy.py` | **27/16**, the pass-4 state, untouched this pass |

The four lines were mapped to their enclosing functions by AST span, not by the line numbers in the
dispatch: `test_an_evaluated_exact_queryset_is_windowed_from_the_rows_it_holds` (2224),
`test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds` (2251, below
`assert materialized_rows(rebuilt) is held` as dispatched),
`test_an_evaluated_exact_queryset_is_windowed_from_its_own_rows_when_awaited` (2295, `AsyncFunctionDef`)
and `test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited` (2311,
`AsyncFunctionDef`). The four named node ids and nothing else. The declined row
`test_a_coordinate_window_over_an_evaluated_project_queryset_class_reads_carried_rows` (2257) has no
type assertion, as the disposition intended, and the reconstruction proves it is otherwise untouched.

`grep -n "type(rows) is"` over the file now reads **9**: five `is QuerySet` on the unevaluated arm
(2001, 2013, 2025, 2061, 2081) and the four `is list` added here. No other tracked `.py` in the
repo carries that assertion shape (population: 209 tracked test files swept; the nine hits are all
in this one file), so no sibling tree is stranded.

### The four rows can fail - proved by running the rows themselves, not a copy of their bodies

Worker 2 owed no failability proof (no boundary), and its two warrants are sound as far as they go:
the contrasting `type(rows) is QuerySet` rows mean no single return type satisfies both arms, and
Worker 1's scratch probe discriminates. Neither of them, though, runs **these four node ids** and
watches **the added line** fail. That was measured here, with no edit to any tracked source file.

Instrument: `docs/builder/temp-tests/050/row_carry/test_w3_pass5_rows_can_fail.py` imports
`tests/test_resource_policy.py` as a module, calls each of the four permanent test functions
directly (fixtures passed in; the two async ones through `async_to_sync`), and runs each twice -
once unregressed, once with `resource_policy.normalized_row_source` monkeypatched to answer with a
`tuple` of the carried rows. A tuple is the exact regression Worker 1's disposition named as
surviving the pre-pass-5 assertions.

| Row | unregressed | under the tuple regression |
|---|---|---|
| sync exact | passes | raises on `assert type(rows) is list` |
| sync project-queryset class | passes | raises on `assert type(rows) is list` |
| async exact | passes | raises on `assert type(rows) is list` |
| async project-queryset class | passes | raises on `assert type(rows) is list` |

**8 passed**, `uv run pytest -c pytest.ini -n0 --no-cov -q -p no:cacheprovider docs/builder/temp-tests/050/row_carry/test_w3_pass5_rows_can_fail.py`.
Which assertion raised is read off the traceback's last entry (`entry.statement` is literally
`assert type(rows) is list`, and its line is one of 2224 / 2251 / 2295 / 2311) rather than off the
exception message: the permanent module is **imported, not collected**, so pytest never rewrites its
bare asserts and `str(AssertionError())` is the empty string. An earlier version of this probe
asserted on the message and reported four failures against rows that had in fact raised exactly as
intended - the empty message is the instrument lying, not the rows.

The companion probe `test_w3_pass5_added_assertion_can_fail.py` (**3 passed**) separates the added
line's contribution at the seam: under the same tuple regression `list(rows) == held[:2]` still
passes, `[row is held[index] ...] == [True, True]` still passes and the query count is still 0, so
the added assertion is the **only** oracle in those rows that catches it. Its third row is the
negative control - an unevaluated source through the same `bounded_rows` comes back `QuerySet` and
`is not list`, so the assertion is contingent on the state each row sets up rather than true of
whatever the helper returns.

### Gates

- `uv run pytest -n0 tests/test_resource_policy.py --no-cov -q` - **288 passed**, exit 0, the count
  the last four passes recorded. Assertions were added to existing rows, not rows, so an unchanged
  collected count is the expected reading.
- The four node ids as their own selection - **4 passed, 4 collected**.
- `uvx pre-commit run --files tests/test_resource_policy.py` - all six hooks **Passed**, first run,
  no rewrite.
- `git status --short` - byte-identical population to the one passes 2-5 recorded; no new tracked
  path, and `docs/builder/temp-tests/` is gitignored. `examples/fakeshop/db.sqlite3` md5
  `2732e633f3303c55aac9d9f398e48df7` before and after every command in this historical pass. Its
  snapshot `HEAD` was `20646db2` throughout.

### DRY findings

None. Four one-line assertions in four rows is not duplication to consolidate: each names one row's
own verdict, and the spelling is the one the five unevaluated-arm rows already use. `type(...) is`
rather than `isinstance` matches the package's own `_bounds_by_its_own_slice` exact-type test, so
the oracle and the code under it agree on what "the type" means.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** (0 lines). No public export
changed; this pass touches one test file.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- The insertion was made by **asserted-unique anchor count** (4 occurrences proved before anything
  was written), not by the dispatch's line numbers, and the declined coordinate-window row is
  outside that population because its anchor is `held[1:3]`. That is the enumerate-before-writing
  discipline, and it is why the placement is exactly right in all four rows.
- Measuring the diffstat on **both** sides of the edit (204/5 then 208/5) is the reading that
  distinguishes four additions from four rewrites; this review reproduced the 204/5 independently
  by reconstruction.
- The pass-4 escalation is discharged: the newly public promise about the evaluated arm's returned
  type is now pinned by four permanent rows instead of by temp files `clean_up.py` deletes.

### Temp test verification

- `docs/builder/temp-tests/050/row_carry/test_w3_pass5_rows_can_fail.py` - runs the four permanent
  rows under the tuple regression; 8 passed.
- `docs/builder/temp-tests/050/row_carry/test_w3_pass5_added_assertion_can_fail.py` - seam-level
  discrimination plus the unevaluated negative control; 3 passed.
- Disposition: **neither is promoted, and neither needs to be.** They are instruments that measure
  the permanent rows; what they prove is that `tests/test_resource_policy.py`'s four new lines are
  the permanent pin. They catch no bug. Both are gitignored and die with the cycle.
- Both import `tests/test_resource_policy.py` by path and register it in `sys.modules` under a
  private name, so run them alone: collected alongside the real module they would build the same
  Strawberry types twice. They were run alone.

### Notes for Worker 1 (spec reconciliation)

None. No behavior, boundary, expectation or public surface changed; the spec slice checklist boxes
are unaffected by a pass that adds assertions to existing rows. The routed and deferred items in
`### Deferred and routed items: every one has a named owner` were re-checked as unmoved at this same
`HEAD` and none is touched by this diff.

### Review outcome

`review-accepted`. The dispatch landed exactly as written - four lines, four named node ids, each
immediately above its anchor, nothing else in the file - the four rows pass and were proved to fail
when the type they assert changes, and every gate is green.

---

## Final verification (Worker 1, pass 4)

Scope: the pass-5 four-line pin, and the two audits this closing pass owes whatever the diff size -
the `### Spec slice checklist (verbatim)` boxes and the routed-item owners. Everything executable in
the cohort was verified at passes 1 and 2 and re-verified at 3; this diff touches one test file.

- **The delta is exactly +4/0 against my pass-3 diffstat, measured by reconstruction rather than
  read.** The working file was copied, the four occurrences of the exact line
  `    assert type(rows) is list` removed, and the remainder diffed against
  `git show HEAD:tests/test_resource_policy.py` (written to scratch; never a checkout).

  | Measurement | Result | Expected |
  |---|---|---|
  | `git diff HEAD --stat -- tests/test_resource_policy.py` now | **208 insertions, 5 deletions** | 208 / 5 |
  | WORK minus the four inserted lines, vs HEAD | **204 insertions, 5 deletions** | the pass-3 state |
  | occurrences of the inserted line at HEAD | **0** | 0 |
  | `git diff HEAD --stat -- django_strawberry_framework/resource_policy.py` | **27 / 16** | the pass-4 state, untouched |
  | control: PRIOR with one further existing line removed | **203 / 5** | must NOT read 204 / 5 |

  The deletion count holding at 5 on both sides is what separates four ADDED lines from four added
  plus one rewritten; the 203/5 control is what proves the reconstruction is sensitive at all, so the
  204/5 row is a measurement and not an arithmetic coincidence.

- **Each line sits above its `held[:2]` anchor, in the four named node ids**, mapped by AST span
  rather than by the line numbers in my own dispatch (those were pin-at-write-time hints and the file
  has since been formatted):

  | Inserted line | Enclosing node, by AST span | Node kind |
  |---|---|---|
  | 2224 | `test_an_evaluated_exact_queryset_is_windowed_from_the_rows_it_holds` | `FunctionDef` |
  | 2251 | `test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds` | `FunctionDef` |
  | 2295 | `test_an_evaluated_exact_queryset_is_windowed_from_its_own_rows_when_awaited` | `AsyncFunctionDef` |
  | 2311 | `test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited` | `AsyncFunctionDef` |

  Anchor occurrences of `    assert list(rows) == held[:2]`: **4**, at 2225 / 2252 / 2296 / 2312.
  Every insert immediately precedes an anchor: **True**. Anchors with no insert above them: **0**.
  The four node ids are the four dispatched ones, in dispatch order, and no fifth row was touched.
  `type(rows) is` over the file reads **9**: the five `is QuerySet` rows on the unevaluated arm
  (2001, 2013, 2025, 2061, 2081) and these four.

- **The four lines actually EXECUTE**, which neither a diffstat nor an AST map can show. A scratch
  `sys.settrace` / `threading.settrace` plugin (`<scratch>/w1p4/tracelines.py`, loaded with `-p`, no
  edit to any tracked file) recorded the watched lines reached while the four node ids ran:
  **[2224, 2251, 2295, 2311] of [2224, 2251, 2295, 2311]**, 4 passed. `threading.settrace` is why the
  two awaited rows report - their body runs on a `sync_to_async` worker thread. Control: the same run
  with line 2270 added to the watch set (inside the declined coordinate-window row, not in the
  selection) reported **4 of 5**, so the instrument can report a line it never reaches. A green row
  whose new assertion sat after an early return would have looked identical without this.

- **The pass-3 negative control re-run at this working tree**, unchanged:
  `uv run pytest -c pytest.ini -n0 --no-cov -q -p no:cacheprovider <scratch>/w1p3/test_w1p3_probe.py`
  - **6 passed**. Its `test_negative_control_unevaluated_is_not_a_list` asserts an unevaluated source
  through the same `bounded_rows` comes back `QuerySet` and `is not list`, so the dispatched
  assertion is contingent on the state each row builds rather than true of whatever the helper
  returns. The probe is scratch, is not promoted, and dies with the cycle; the permanent contrasting
  verdict is the five `type(rows) is QuerySet` rows above.

- **Gates.** `uv run pytest -n0 tests/test_resource_policy.py --no-cov -q` - **288 passed**, exit 0,
  no `--cov*` flag; the same 288 the last four passes recorded, which is the expected reading for a
  pass that adds assertions to existing rows rather than rows. The four node ids as their own
  selection - **4 passed, 4 collected**, so the ids are real and spelled correctly.
  `uvx pre-commit run --files tests/test_resource_policy.py` - all six hooks **Passed** on the FIRST
  run, no rewrite, no re-stage (the `kanban anchors` hook, which reported a spurious first-run
  failure in two earlier passes off the concurrently-written board DB, did not this time).
  Staged-anchor sweep: `TODO(spec-` over 425 `.py` files under `django_strawberry_framework/`,
  `tests/` and `examples/` returns **2 anchors, neither naming spec-050** (`spec-035` in
  `test_library_api.py`, `spec-060` in `filters/sets.py`), with a positive control showing the same
  instrument finds plain `TODO` hits.

- **Spec slice checklist: both boxes remain `- [x]` and both remain true.** Re-verified, not carried:
  each box's text was cut from the artifact, whitespace-flattened and counted against the CURRENT
  `docs/spec-050-list_field_arguments-0_0_15.md` - **1 occurrence each** (measured before P2-2; 0 at `f7192bfb` and HEAD), so the text a tick is
  audited against is still the text the spec demands after every `### Spec changes made (Worker 1
  only)` edit. Every row the clause-by-clause tick warrant names still collects:
  `test_a_project_queryset_class_relation_costs_what_djangos_own_manager_costs[two-parents]` and
  `[three-parents]` (renamed by P2-2 to `…costs_two_prefetch_queries`, one arm), `test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited`
  (all three in `examples/fakeshop/test_query/test_resource_policy_api.py`),
  `test_a_subclass_result_with_a_pending_deferred_filter_seals_with_it_baked`, and both
  `[malformed-deferred-filter]` rows. The absolute-count clause is carried by
  `CARRY_RELATION_QUERIES = 2` asserted on BOTH the control and the mounted arm at both parent
  cardinalities, which is the reading the carry-forward from my first pass asked for - an equality
  between two live counts alone would have been vacuous. Nothing deferred, nothing over-ticked.

- **Every routed item still carries a named owner, and every routed replacement is still a paste.**
  Re-derived at this HEAD by cutting each blockquote out of this artifact by line span and counting
  it whitespace-flattened against the target file, so no hand transcription stands between the record
  and the measurement:

  | Routed item | Owner | Old text | Replacement |
  |---|---|---|---|
  | `docs/GLOSSARY.md` "Sealed execution queryset" body | `maintainer`, Worker 0's card-close DB pass | **1** | **0** (discharged in substance since) |
  | `docs/GLOSSARY.md` `DjangoListField` body (`djangolistfield` anchor) | `maintainer`, same DB pass | **1** | **0** (discharged since) |
  | `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` #"unresolved deferred filter, unsealable prefetch child" | `maintainer` | **1** | n/a |
  | `docs/SPECS/spec-034-permissions-0_0_10.md` #"an unresolved deferred filter" | `maintainer` | **1** | n/a |
  | `docs/SPECS/spec-047-resource_policy-0_0_14.md` #"The bound is applied by SLICING" | `maintainer` (recorded reading: a dated `0.0.14` record; amended by `b3458ee8`) | **1** | n/a |
  | Robustness row - an exact `QuerySet` carrying a foreign `_result_cache` | `maintainer`, the DONE record's catalog, not `BACKLOG.md` | pre-existing at HEAD | n/a |
  | `_UNRECOMPOSED_CHILD_POLICY` has no production reader after `fd39cac6` | `maintainer` (delete-or-correct) | unchanged (retired by `4d9f1c3d`) | n/a |
  | Decision 20's connection-field separation | `maintainer`, on a new card once a number exists | recorded in the rationale (discharged by `fee87ac4`/`c87f4f98`, card 053) | n/a |

  Control: a needle present in no file counts **0** against the same flattened reader. Eight items,
  eight named owners, none unhomed.

- **DRY, fail-open and public surface.** No new duplication: four one-line assertions each state one
  row's own verdict in the spelling the five unevaluated-arm rows already use, and `type(...) is`
  rather than `isinstance` is the package's own exact-type test at `_bounds_by_its_own_slice`. No
  fail-open shape can land in an assertion, and none did. `git diff HEAD --
  django_strawberry_framework/__init__.py` is empty.

- **Concurrent work, stop-and-report.** `examples/fakeshop/db.sqlite3` md5
  `2732e633f3303c55aac9d9f398e48df7` before and after every command in this pass, the same value every
  pass since pass 2 recorded; the historical snapshot's `HEAD` was `20646db2` throughout.
  `git status --short` was the identical
  population - line for line - that passes 2 through 5 recorded: the concurrent session's
  `tests/mutations/*`, `django_strawberry_framework/{permissions,schema,types/resolvers,utils/querysets}.py`,
  the live example suites, `docs/{README,TREE,feedback}.md`, `examples/fakeshop/test_query/README.md`,
  the `docs/bug_hunt/*` delete-and-rename pair,
  `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`, plus this cohort's own files and the
  spec pair. No new path appeared. Nothing touched, nothing reverted.

- **Final status:** superseded cohort artifact; `final-accepted` only for the historical
  pre-candidate snapshot.

### Summary

Cohort A ships the evaluation-state carry at the raw-list seam - a source that arrives evaluated is
windowed from the rows it already holds, exact queryset and rebuilt project queryset class alike,
with the query count pinned at an absolute zero in the package tier and a `Manager.from_queryset`
relation pinned live at Django's own manager's absolute count at two parent cardinalities - together
with the sealer admission that made the subclass reachable (the class-identity gate deleted, the
pending reverse-relation predicate baked by Django's own unbound `Query.add_q`, a deferred-filter
state Django never writes refused with the typed error at both tiers) and the docstrings on
`bounded_rows`, `_windowed_rows`, `normalized_row_source`, `materialized_rows` and
`_prepared_visibility_source` corrected to the shipped behavior. The last open item, the returned
type that `bounded_rows`' public docstring now promises for an evaluated source, is pinned by four
permanent assertions instead of by temp files `clean_up.py` deletes. Both `### Spec slice checklist
(verbatim)` boxes are ticked and true; nothing is deferred without an owner.

### Spec changes made (Worker 1 only)

None this pass. The diff is four assertions in one test file: no behavior, boundary, expectation or
public surface changed, both `## Definition of done` rows amended at pass 2 remain accurate, and no
home in the spec or the rationale claims the evaluated arm's returned type, so nothing the pin lands
was falsified or is now under-stated. The spec's header and `Status:` lines were re-read this spawn
(the per-spawn duty) and still describe the carry and the admission as the current contract.

The eight routed items in the table above are the cohort's complete open set; all eight are the
maintainer's, seven of them in Worker 0's card-close board/glossary DB pass.

## Build report (Worker 3) — P2-2 public manager declaration repair (no review pass followed)

The earlier live carry rows were superseded: their temporary `_meta.local_managers` mount and
private `_expire_cache()` calls proved a manager class, but did not dogfood a supported project
declaration. The repair makes the fakeshop model itself the acceptance fixture.

### Implementation

- `examples/fakeshop/apps/library/models.py` now declares a no-op `LoanQuerySet` and assigns
  `objects = LoanQuerySet.as_manager()` on `Loan`. Django's dynamic manager keeps its existing
  `use_in_migrations=False` default, so the declaration changes runtime manager behavior without
  adding migration state.
- `examples/fakeshop/test_query/test_resource_policy_api.py` removes `_ProjectLoanQuerySet`, the
  generated temporary manager, the `_meta.local_managers` / `_expire_cache()` context manager,
  and the parallel control/mounted schemas. The sync live row runs the existing document against
  the ordinary model declaration and asserts the absolute two-query prefetch cost at two and
  three parent cardinalities. The async row uses the same ordinary declaration and retains its
  exact payload assertion.
- `docs/spec-050-list_field_arguments-0_0_15.md` updates Decision 8's dogfood note, Slice 3's
  row, the raw-list live test plan, and the Definition-of-done row to name the model declaration
  and the migration-safe check. No package-tier mechanism row was removed: the private
  `_apply_rel_filters` construction remains only where it proves the package's deferred-predicate
  rebuild invariant, which the live wire test cannot isolate.

### Acceptance disposition

The supported project shape is now reached through Django's public model declaration. The old
mount and control arms are historical evidence only; the current acceptance contract is the
ordinary `LoanQuerySet.as_manager()` model, two absolute queries for both parent cardinalities,
and the async payload.

### Validation run

- `UV_CACHE_DIR=/private/tmp/codex-uv-cache uv run ruff format .` - 451 files unchanged.
- `UV_CACHE_DIR=/private/tmp/codex-uv-cache uv run ruff check --fix .` - all checks passed.
- `UV_CACHE_DIR=/private/tmp/codex-uv-cache uv run python examples/fakeshop/manage.py check` - no
  issues.
- `UV_CACHE_DIR=/private/tmp/codex-uv-cache uv run python examples/fakeshop/manage.py makemigrations
  --check --dry-run` - no changes detected.
- Trailing-comma/source-layout, citation, and spec glossary checks passed; the glossary checker
  reports 43 terms with all entries and links present.
- A direct non-pytest `/graphql/` probe over a seeded database (the tracked `db.sqlite3` holds no `library_patron` rows) returned
  status 200,
  no errors, six patrons, and exactly two queries. A metadata probe confirmed the default and
  reverse relation querysets are `LoanQuerySet`, the manager has `use_in_migrations=False`, and
  Django leaves the reverse predicate pending for the package sealer.

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
