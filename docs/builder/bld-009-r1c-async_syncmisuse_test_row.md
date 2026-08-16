# Build: R1c — Promote the async `SyncMisuseError` row to a permanent test

Spec reference: `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (context only; this item edits no spec)
Contract: `docs/builder/build-009-rich_schema_architecture-0_0_4.md` `### Maintainer decision 5`
Status: final-accepted

## Plan (Worker 1)

Planning pass run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. HEAD re-derived at the start of the pass:
**`6f8bf818`** (the dispatch's "last seen" hash, re-derived rather than trusted). This item is the
cycle's **only** code-writing item and therefore the only one running the full
`W1 -> W2 -> W3 -> W1` chain (build plan `## Artifact list`, per-item chain table).

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`): read
`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:1-14`. The title, the rationale-companion
pointer at `:3` (which already enumerates the six scrubbed mechanisms), and `## Purpose` at `:5-14`
all still describe the build's current state. R1c falsifies nothing in them and writes no spec text.
No edit owed; `### Spec changes made (Worker 1 only)` will record `None.` unless the build surfaces
something.

### The gap, and the fact it turns on

`tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse` (`:1109-1124`)
pins `SyncMisuseError` for an `async def get_queryset` **only under `execute_sync`**. No permanent
row pins the same outcome for a **default** `DjangoConnectionField` under `await schema.execute`.

That distinction is load-bearing, and it is the exact fact R1's `:417` correction turned on:

- `connection.py::_build_connection_resolver` (`:1888`) fixes the sync/async pipeline choice at
  **construction**, not per execution. `resolver is None` (`:1947`), the async-generator branch
  (`:1958`), and the plain-`def` branch (the `else:` at `:1989`) all emit a **sync** `def _resolve`
  calling `_pipeline_sync`; only `is_async_callable(resolver)` (`:1976`) yields the `async def` branch that
  awaits `_pipeline_async`. The module states the consequence itself:
  `connection.py::_build_connection_resolver` #"to drive an async ``get_queryset`` hook through a
  connection, supply an ``async def`` ``resolver=``".
- The nested relation-connection builder has **no async sibling at all** (`connection.py:2154` calls
  `_pipeline_sync` unconditionally).
- So a default connection field runs the **sync** pipeline even under async execution, and
  `utils/querysets.py::apply_type_visibility_sync` -> `reject_async_in_sync_context` (`:2991`)
  raises `SyncMisuseError` rather than awaiting the hook.

A ready-made, passing body exists at
`docs/builder/temp-tests/r1/test_async_execution_default_connection.py`. It is the starting point,
not the final shape: most of the adjustments below are forced by the target module's own
conventions rather than chosen, and each is attributed where it is decided.

### DRY analysis

**Helper inventory checked.** The package-wide AST inventory was refreshed this pass over the whole
of `django_strawberry_framework/` (not `utils/` alone), written to `docs/shadow/helper-inventory.md`
(**1,880 lines**) with the command in `worker-1.md` `### Package-wide helper inventory before helper
planning`. Grepped for the shapes this item needs — `misuse`, `reject_async`,
`apply_type_visibility`, `in_async_context`, `is_async_callable`, `async_context` — **eight** hits
(count taken from the grep output, not from the bullet list below), each opened at source:

- `utils/querysets.py::SyncMisuseError` (`:116`) — the typed marker the row asserts on.
- `utils/querysets.py::reject_async_in_sync_context` (`:153`) — the guard; **the boundary the row
  pins**. Raise site at `:182`.
- `utils/querysets.py::apply_type_visibility_sync` (`:2929`) / `apply_type_visibility_async`
  (`:3205`) — the colored pair; the sync one calls the guard at `:2991`.
- `utils/typing.py::is_async_callable` (`:1801` of the inventory) — the construction-time predicate
  that decides the branch. Read, **not used by the test** (see "Duplication risk avoided").
- `filters/sets.py::FilterSet.apply`, `utils/querysets.py::sync_pipeline_recourse`,
  `utils/querysets.py::require_write_pipeline` — adjacent, not on this row's path.

**Existing patterns reused.** Everything this row needs already exists in the target module; the item
adds no helper of any kind.

- `tests/test_connection.py:441-470` `_make_sidecar_node_type(name, *, total_count, filterset,
  orderset, get_queryset)` — builds a throwaway Relay-Node `DjangoType` over `Category` and installs
  `get_queryset` as a classmethod. Its docstring already names this use ("so the visibility hook /
  ``SyncMisuseError`` paths can be exercised").
- `tests/test_connection.py:473-502` `_field_schema(node_type, *, resolver=None, ...)` — builds the
  in-process schema exposing `items` via `DjangoConnectionField(node_type, resolver=resolver)`.
  **`resolver` defaults to `None`, which is exactly the default-field branch under test.**
- `tests/test_connection.py:1109-1124` — the sync sibling, whose shape the new row mirrors line for
  line except for the execution color.
- `tests/test_connection.py:1724-1742`
  `test_connection_hostile_hook_narrows_edges_and_total_count_async` — the closest structural
  precedent: a **default** connection field (no `resolver=`) with a **sync** `get_queryset` under
  `await schema.execute`, which succeeds. The new row is its negative twin.
- The module's async-row convention, enumerated by AST rather than by eye (all nine `async def
  test_*` rows walked; script output reproduced in `### Decision 3`): a **function-local**
  `from asgiref.sync import sync_to_async` at `:411`, `:826`, `:1014`, `:1481`, `:1727`, `:1879`
  (six sites, cross-checked against `docs/shadow/tests__test_connection.overview.md` "Imports"),
  then `await sync_to_async(services.seed_data)(N)` and `await sync_to_async(<builder>)(...)`. The
  split is **not** uniform and the rule behind it is exact — see `### Decision 3`.
- `apps.products.services.seed_data` — `AGENTS.md` rule 8's first-line seeding helper, already
  imported at `tests/test_connection.py:31`.

**New helpers justified.** **None.** No new test helper, fixture, constant, or package symbol. The
row is one function reusing two module-private builders and one seeding helper. The condition that
would justify extracting an async-execution helper later: if two or more further
`sync_to_async(_field_schema)` + `await schema.execute` rows land whose *setup* (not just their
assertions) is identical — today the six wrapped sites differ in seeding, sidecars, resolver, and
`context_value`, so a helper would abstract over variation rather than duplication.

**Duplication risk avoided.** Four near-copies a naive implementation would introduce, each
prevented by a named decision:

1. **A cross-module import of private helpers.** The temp body does
   `from tests.test_connection import _field_schema, _make_sidecar_node_type` — a second module
   reaching into another test module's privates. Same-file placement deletes the import outright.
   This is the single strongest argument for placement (see below).
2. **Re-imported module-level names.** The temp body re-imports `pytest`, `SyncMisuseError`
   (`:61`), and `services` (`:31`) — all three already at the target module's header. The row adds
   **zero** module-level imports; its only import is the function-local `sync_to_async` the six
   sibling rows use.
3. **A hoisted `sync_to_async` import.** Tempting (six local copies today, seven once this row
   lands) and **rejected**: it would
   edit a module header a concurrent session is actively writing, it would be a seven-site refactor
   outside this item's contract, and the locality is deliberate (an async-only dependency kept off
   the sync import surface). Condition that would change the answer: a module-level `sync_to_async`
   import landing for an unrelated reason, after which the seven locals collapse into it in one
   pass.
4. **A hand-rolled async-execution schema builder.** `_field_schema` already does it; the row must
   not build a `strawberry.Schema` inline.

**Existence challenge.** Should this row exist at all, given the sync sibling? Yes, and the reason
is precise: no `execute_sync` row can observe whether async execution would have taken a *different*
(async) pipeline. The sibling's green result is compatible with a world in which the default field
acquires an async pipeline under async execution; this row is the only thing that refutes it.
Recorded here so Worker 3 does not have to re-derive it, and so the two rows are never collapsed.

### Decision 1 — Placement, justified against `AGENTS.md` rule 10

**File:** `tests/test_connection.py` (package tier).
**Function:** `test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`.
**Position:** immediately after `test_sync_context_async_get_queryset_raises_sync_misuse`
(currently ending `:1124`), before
`test_connection_sync_resolver_returning_coroutine_raises_sync_misuse` (`:1127`).

**[Final-verification amendment 1, Worker 1, 2026-08-16.** The grounds below are the corrected set.
As dispatched to Worker 2 this decision rested on three grounds and asserted "Grounds 1 and 2 are
each independently sufficient". Worker 3 disproved ground 2 by grep and I re-derived it: the live
tier **does** carry an async execution colour — `_probe_async_view` mounts
`AsyncDjangoGraphQLView` on a real event loop at `examples/fakeshop/test_query/test_error_policy_api.py:192`
and `examples/fakeshop/test_query/test_resource_policy_api.py:124`, and
`examples/fakeshop/test_query/test_transport_api.py` mounts the same view at `:239`, `:381`, `:398`.
Ground 1 was overstated for the same reason: a probe schema is that tier's normal mechanism for
hosting a fixture the shipped schema cannot. Ground 2 is therefore **withdrawn**, ground 1 is
narrowed to fakeshop's *shipped* types, and the decisive ground Worker 3 supplied is added as
ground 0. **The placement outcome is unchanged and no test change is owed** — the row's contract,
assertions, and file are exactly what the builder implemented against.**]**

`AGENTS.md` rule 10 requires any line reachable via a real GraphQL query against fakeshop to be
covered in `examples/fakeshop/test_query/`, falling back to the other two trees only when the line
is unreachable from a real query. **The package tier is correct here on the grounds below, of which
ground 0 alone is dispositive:**

0. **Rule 10's obligation is not engaged, because the row earns no new package coverage line.** Rule
   10 and `examples/fakeshop/test_query/README.md`'s coverage rule both attach to a coverage line
   "earned by a real-world GraphQL query against the fakeshop schema"; the raise this row reaches —
   `utils/querysets.py::reject_async_in_sync_context` via
   `utils/querysets.py::apply_type_visibility_sync` — is already covered by the sync sibling. That
   the two rows traverse the *same* package boundary is measured, not argued: failability entry 1's
   node-id set is exactly those two rows and nothing else. What this row adds is a
   **construction-time dispatch** contract, which the same README routes explicitly to the package
   tier ("package-internal coverage such as ... definition-order internals").
1. **The precondition is a misconfiguration, and fakeshop's *shipped* types are correctly
   configured.** The row needs a `DjangoType` whose `get_queryset` is `async def`, exposed through a
   *default* `DjangoConnectionField`. No shipped fakeshop type declares one, and adding one would
   break every other query against that type, since the rest of the live suite drives `/graphql/`
   through `django.test.Client`, i.e. sync execution, where the same hook raises `SyncMisuseError` on
   every request. This bounds the *shipped* schema only — a probe schema could host such a fixture,
   which is why this ground is contributory rather than sufficient.
2. *(withdrawn — see amendment 1. The live tier does carry an async execution colour.)*
3. **The type under test must be throwaway.** `_make_sidecar_node_type` builds a per-test
   `DjangoType` cleared by the module's autouse registry fixture (`:64-76`). Every live probe schema
   reuses fakeshop's already-registered types; none invents one, and a fakeshop app type is
   process-global and shared with every other live row.

Ground 0 is dispositive on its own; grounds 1 and 3 are contributory and survive intact. The middle
tier (`examples/fakeshop/apps/<app>/tests/`) fails on ground 1 for the same reason and additionally
on ownership: the system under test is `django_strawberry_framework.connection`, not an example app.

**Why this file rather than a new package-test file.** The sibling it pairs with lives here, and
pairing an async twin next to its sync original has real value for the next reader: the two rows
read as one contract in two execution colors, which is exactly the fact the cycle found undocumented.
The module already does this twice, enumerated mechanically rather than by eye —
`grep -n '^async def test_.*_async():'` returns exactly two rows, `:1725` and `:1877`, and **each sits
immediately after its sync original**. A separate file would also force the private-helper import
this plan's DRY analysis item 1 exists to prevent.

**Naming.** Those two twins are named by appending `_async` to the sync name, which does not survive
here — the sibling's name opens with `sync_context`, the very thing the twin negates, so appending
would produce a self-contradicting name. The chosen name substitutes
`async_execution_default_connection` for `sync_context` and keeps the
`..._async_get_queryset_raises_sync_misuse` tail byte-identical, so the pair still sorts and greps
together. Line length: `async def <name>():` measures **90** characters, inside the 100 limit.

### Decision 2 — Shape: what is asserted, and why it cannot pass with an async pipeline

`BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability` governs.
The load-bearing property is **"the default connection field takes the sync pipeline even under
async execution"**, not "an error appeared".

**Where it surfaces:** as a **top-level GraphQL error**, not a raised exception. `SyncMisuseError`
is raised inside the resolver, so Strawberry wraps it; the row therefore reads
`result.errors[*].original_error`, exactly as the sync sibling does. **No `pytest.raises`** — that
would pin a different (and false) surfacing.

**The three assertions:**

```python
assert result.errors is not None
assert any(isinstance(err.original_error, SyncMisuseError) for err in result.errors)
assert result.data is None
```

- `isinstance(..., SyncMisuseError)` and not the message text, and not the base `ConfigurationError`:
  `SyncMisuseError` is a `ConfigurationError` subclass (`utils/querysets.py:116`), so asserting the
  base would also pass on the plain-`ConfigurationError` rejections that
  `_normalized_visibility_result` raises for other defects. The subclass is the discriminating
  assertion.
- `result.data is None`: the schema's `items` field is non-null (`_field_schema` annotates
  `"items": conn_type` with no `| None`), so the error propagates to the root. Precedent in-module
  at `test_connection_sync_resolver_returning_coroutine_raises_sync_misuse` (`:1147`). It is the
  direct statement that the async pipeline did **not** quietly run and serve the seeded row.

**Why it cannot pass if the field acquires an async pipeline.** If
`_build_connection_resolver`'s `resolver is None` branch became `async def` + `_pipeline_async`,
then `apply_type_visibility_async` would **await** the hook, the queryset would resolve, and the
query would succeed with one seeded row: `result.errors is None` and `result.data` populated. Both
the first and the third assertion fail. This is proved, not argued, by failability entry 2 below.

**How the row guarantees it is on the DEFAULT path.** Three structural facts, all inside the row:

- `_field_schema(node_type)` is called **with no `resolver=` argument**, so its `resolver=None`
  default flows into `DjangoConnectionField(node_type, resolver=None)` and
  `_build_connection_resolver` takes the `if resolver is None:` branch (`connection.py:1947`). Any
  consumer-resolver argument would route to a different branch and pin a different contract; the
  row must never grow one.
- The query is **minimal** — `{ items { edges { node { id } } } }`: no `filter:`, no `orderBy:`, no
  `totalCount`, no `first`/`last`. Per `BUILD.md`'s right-path rule, a sidecar argument can silently
  route a selection elsewhere, so the query is kept to the one shape that can only take the path it
  claims to test.
- `_make_sidecar_node_type` is called with its **defaults**, exactly as the sync sibling calls it:
  `total_count` defaults `False`, so no generated `totalCount` subclass and no `_attach_count_*`
  path; the `filterset` / `orderset` defaults do attach sidecar classes, but the query above supplies
  neither `filter:` nor `orderBy:`, so no sidecar-apply branch runs. The two rows differ in exactly
  one dimension — the execution color — which is what makes them a twin pair rather than two tests.

**Rejected assertion shape:** an `is_async_callable(field.base_resolver)` introspection assertion on
the constructed field. Rejected because it reaches into private construction state to restate what
the execution already proves, and because it would keep passing if the *pipeline body* changed while
the resolver stayed sync — i.e. it pins the mechanism's spelling rather than its answer.

### Decision 3 — Fixtures, imports, and `django_db`

**The module's async convention, measured rather than eyeballed.** An AST walk of all **nine**
`async def test_*` rows in `tests/test_connection.py` splits them cleanly, and the split is not the
"uniform wrap" a casual read suggests:

| Rows | Builder call | `django_db` marker |
|---|---|---|
| `:409`, `:816`, `:1012`, `:1473`, `:1725`, `:1877` (**6**) | `await sync_to_async(<builder>)(...)` — five wrap `_field_schema`, `:409` wraps its sibling `_schema_for` | `@pytest.mark.django_db(transaction=True)` on every one (decorators `:408`, `:815`, `:1011`, `:1472`, `:1724`, `:1876`) |
| `:1127`, `:1150` (**2**) | `_field_schema(...)` called **directly** | **no marker** — neither row touches the DB |
| `:780` (**1**) | builds no schema | no marker |

**The rule is exact: an async row that touches the database carries `django_db(transaction=True)`
and wraps its builder; one that does not, does neither.** Six of six on the DB-touching side, two of
two on the other, with `:780` outside both. That single fact
decides all three sub-choices below together, and it is why the temp body — which carries the
marker *and* calls directly, the one mixed shape in either class — is not the final shape.

- **Seeding:** first line of the body, `await sync_to_async(services.seed_data)(1)`, mirroring the
  sync sibling's `services.seed_data(1)` and satisfying `AGENTS.md` rule 8 for the catalog tier.
  The wrap is required — a bare sync ORM call from an `async def` body raises
  `SynchronousOnlyOperation`. The seeded row is not incidental: it is what makes
  `assert result.data is None` discriminating, since an async pipeline would have served it.
  Seeding is also what puts this row in the DB-touching class, which fixes the next two choices.
- **`django_db`:** `@pytest.mark.django_db(transaction=True)`, as the temp body has it and as all
  six DB-touching async siblings do. `transaction=True` is what the async-sqlite connection-teardown
  discipline in `tests/conftest.py:91` `_close_context_local_db_connections` is built around. A
  measurement that the row also passes without the marker is **not** a licence to drop it — dropping
  it would mean dropping the seeding, and rule 8 wants the seeding.
- **Schema construction:** `schema = await sync_to_async(_field_schema)(node_type)`, per the
  six-of-six rule for this class. The temp body's direct call happens to work (the builder does no
  ORM work today), but the two direct-call rows it resembles are precisely the two that carry no
  marker and no seeding. Wrapping costs nothing here — the local `sync_to_async` import is already
  needed for the seed — and keeps the row inside the class it actually belongs to.
- **Imports:** **no new module-level import.** `pytest` (`:28`), `services` (`:31`), and
  `SyncMisuseError` (`:61`) are already at the header. The only import is the function-local
  `from asgiref.sync import sync_to_async` the six sibling rows use.
- **Throwaway type name:** must be unique across the module (the autouse registry fixture clears
  between tests, but a duplicated `Meta.name` inside one module is a readability trap).
  `AsyncVisibilityAsyncExecNode` is free — verify with `grep -c` before writing. The sync sibling
  uses `AsyncVisibilitySyncNode`; the pairing is intentional.
- **Hook signature:** `async def get_queryset(cls, qs, info): return qs` — installed as a classmethod
  by `_make_sidecar_node_type`, identical to the sync sibling's. The body deliberately does nothing:
  the contract is that the hook is **refused**, so a hook that filtered would only add a way for the
  row to fail for the wrong reason.

### Decision 4 — Failability proofs (mandatory; two entries)

`BUILD.md` `## Failability proofs: prove the test can fail` governs; `### Maintainer decision 5`
requires the proof for this item. This row pins a **pre-existing** production boundary rather than
introducing one, which is why the proof is the ideal shape here.

**Perform them with `scripts/prove_failability.py`** — `BUILD.md` `### Mechanized` names it the
supported way, and it runs the anchor check, the pre-mutation baseline, the row listing, the restore
and the byte-comparison in order, refusing the shortcuts. Manifest home:
`docs/builder/temp-tests/r1c/proofs.json`. **Read `--help` for the manifest schema and flags** — it
owns them; this plan deliberately does not restate them. The fenced fallback loop in `BUILD.md` is
the alternative if the tool cannot express an entry.

**[Final-verification amendment 2, Worker 1, 2026-08-16 — the focused scope, folded in with the
correct licence.** As dispatched, both entries' `**Focused scope:**` read
`uv run pytest tests/test_connection.py --no-cov`; both were actually run at
`tests/test_connection.py -n0 -p no:randomly -W ignore::RuntimeWarning`. The drift is endorsed, and
the bullets below now carry the scope as run. **Its licence is non-determinism, not a
collection/setup error.** Worker 2's build report justified the `-W` filter by saying the unfiltered
run produces a warnings-as-errors *teardown error*, which `BUILD.md` `### What gets recorded` grades
as no valid count; Worker 3 ran the unfiltered control at the same `-n0` scope and measured
**4 failed, 0 collection/setup errors** — that ERROR shape belongs to `-n auto`, not to the recorded
scope, so the cited licence never applied to it. What the two passes did measure is that the
*artifact rows drift*: Worker 2 saw two extra ids unfiltered
(`test_async_consumer_resolver_iterable_with_total_count_selected_raises`,
`test_connection_type_for_generates_total_count_for_direct_relay_inheritance`), Worker 3 saw two
further ones (`test_connection_resolver_async_dispatch`,
`test_connection_field_omits_args_without_sidecars`) — disjoint sets for the same scope. Since
`BUILD.md` `### What gets recorded` requires a node-id **set**, a set that changes run to run is not
a recordable measurement, and the filter is what makes one exist. The filtered set is a strict subset
containing exactly the two rows that assert on the guard; suppression can only lower a count against
a floor rule; and the warning is manufactured by the mutation, not raised by the shipped tree.
**The flag is proof-local and must never be generalized into a standing invocation.** `pytest.ini`'s
`filterwarnings = error` was not touched by any pass (`git status --porcelain -- pytest.ini
pyproject.toml tests/conftest.py` is empty), and `AGENTS.md`'s async-sqlite discipline — never weaken
`-W error` to make a real warning go away — is untouched by a transient argument on a proof run over
a deliberately broken tree.**]**

**Entry 1 (mandatory) — the guard `### Maintainer decision 5` names.**

- **Boundary:** `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`
  #"result = reject_async_in_sync_context(" — the visibility seam's invocation of
  `utils/querysets.py::reject_async_in_sync_context`, whose raise site is `:182`.
- **Anchor:** `grep -c 'result = reject_async_in_sync_context(' django_strawberry_framework/utils/querysets.py`
  -> **verified 1 this pass** (the only other two occurrences are the `def` at `:153` and a
  docstring mention at `:177`, neither matching the `result = ` prefix). Re-run it before the copy;
  a count other than 1 means a live prior mutation or a concurrent edit — abort having written
  nothing.
- **Mutation:** delete the `result = reject_async_in_sync_context(...)` call entirely, leaving
  `result = type_cls.get_queryset(queryset, info)` to flow straight into
  `_normalized_visibility_result`. That **removes** the boundary; it does not perturb code near it.
- **Focused scope** (amendment 2): `uv run pytest tests/test_connection.py -n0 -p no:randomly
  -W ignore::RuntimeWarning --no-cov`.
- **Expected failing rows — pre-decided, per the dispatch's question.** **At least two**, and the
  sync sibling failing alongside the new row is **expected and correct**:
  `test_async_execution_default_connection_async_get_queryset_raises_sync_misuse` **and**
  `test_sync_context_async_get_queryset_raises_sync_misuse`. Both drive
  `apply_type_visibility_sync`; both assert the `SyncMisuseError` subclass, and with the guard gone
  the coroutine reaches `_normalized_visibility_result` and is rejected as a plain
  `ConfigurationError`, which the `isinstance` assertion refuses. Two rows clears the weakly-pinned
  threshold (`BUILD.md` `### Acceptance rule`: **0 or 1 is `revision-needed`**).
  - If **only the new row** fails: the sibling was skipped, deselected, or collection-errored.
    Investigate and re-run — do **not** record it as a one-row result, and do **not** treat the
    number as the boundary's pinning strength until the collection/setup error count is 0.
  - If **only the sibling** fails: the new row is not pinning this boundary. That is a defect in the
    row, not in the proof — `revision-needed`.
  - If **0 or 1** rows fail with 0 collection errors: weakly pinned, `revision-needed`; the remedy
    is more or better-targeted rows, never a weaker boundary and never a recorded exception.
- Unrelated `tests/test_connection.py` rows are unaffected: `_require_async_iterable_context`'s own
  raise (`connection.py:1941`) is a different boundary and is not touched.

**Entry 2 (required) — the construction-time pipeline choice, which is what makes the NEW row
non-redundant.**

Entry 1 alone cannot distinguish the new row from the sibling that already existed — under it both
fail for the same reason. That is precisely the gap Worker 3 would (rightly) raise, so the plan
closes it up front.

- **Boundary:** `django_strawberry_framework/connection.py::_build_connection_resolver` #"if
  resolver is None:" (`:1947`) — the default branch's commitment to a **sync** `_resolve` running
  `_pipeline_sync` (`:1951`).
- **Anchor:** `grep -c 'if resolver is None:' django_strawberry_framework/connection.py` ->
  **verified 1 this pass**.
- **Mutation:** convert that branch's `def _resolve` to `async def _resolve` and its
  `return _pipeline_sync(...)` to `return await _pipeline_async(...)` — i.e. give the default field
  the async pipeline the contract says it does not get.
- **Focused scope** (amendment 2): the same `uv run pytest tests/test_connection.py -n0
  -p no:randomly -W ignore::RuntimeWarning --no-cov`, kept byte-identical to entry 1's so the
  node-id **sets** are differenced rather than the counts compared.
- **Expected:** a large failing set (every `execute_sync` row against a default field now meets an
  async resolver). The pass/fail question for this entry is narrower and is the whole point:
  **the new row must be among the failures**, and its failure mode must be
  `assert result.errors is not None` / `assert result.data is None` — i.e. *the query succeeded*.
  Record that failure mode explicitly in the entry; it is the evidence that this row, and nothing
  else in the suite, pins "async execution does not get a different pipeline". A large row count
  does not excuse omitting it.

**Both entries, in order, one at a time.** `BUILD.md` `### Mutations are transient`: revert entry 1
and prove the revert **before** starting entry 2. Never leave a mutation across a `Status:`
transition and never hand a mutated tree to Worker 3.

**Concurrent-writer hazard — read this before the first `cp`.** Both target files are dirty under a
concurrent package-source session (`git status --porcelain -- django_strawberry_framework/connection.py
django_strawberry_framework/utils/querysets.py` -> both `M` at this planning pass). The proof loop's
restore is a `cp` of a pre-mutation copy, so a concurrent write landing **inside** a mutation window
would be destroyed by it.

- Record `shasum` of each target immediately **before** its mutation and immediately **after** the
  restore, and put both in the artifact entry.
- Keep each window as short as possible: mutate, run, restore. Nothing else between.
- If at restore time the file's content is neither the mutated content nor the pre-mutation copy, a
  third party wrote inside the window: **do not `cp`-restore.** Reverse only your own bytes with the
  inverse edit, then **stop and report to Worker 0** (`ARTIFACT.md` `### Validation run`:
  stop-and-report, never a revert).
- `git stash` / `checkout` / `restore` / `worktree` are banned repo-wide in this cycle and are never
  part of a restore.
- `git diff -- <file>` is **not** the revert proof on this tree and never can be — the files carry
  another session's work at HEAD-delta. The `cmp` against the out-of-repo pre-mutation copy is the
  proof.

### Decision 5 — Floor verification

`### Maintainer decision 5` puts R1c in scope and **amends the build plan's blanket
`Floor-verification scope: none` for this item alone**: the row exercises a Django / Strawberry
async-execution seam, which `BUILD.md` `## Floor verification` `### When it is required` names
explicitly.

- **Floor versions:** taken from `BUILD.md` `## Floor verification`, which that document states is
  **the single canonical statement of the floor versions** — Django **5.2.16** on Python **3.10**
  with strawberry-graphql **0.316.0**. Not restated from memory and not taken from any other
  document. Re-read that section before building the venv in case it has moved.
- **Owning pass: Worker 2** (the build pass), per `### Maintainer decision 5` and the build plan's
  per-item chain table. The final gate is the backstop that confirms it happened, not a second owner.
- **Focused scope at the floor** — the two node ids, and nothing wider (this is not a second sweep):
  - `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`
  - `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse`
  The sibling rides along because the pair *is* the contract: the floor question is whether both
  execution colors still reach the same guard on the oldest supported stack.
- **Procedure:** `BUILD.md` `### How to build the floor venv`, verbatim — an isolated venv under a
  scratch path **outside** the repo, `uv pip install --python <venv>/bin/python` for every install.
  **Never mutate the shared `.venv`**; `uv pip install` ignores `UV_PROJECT_ENVIRONMENT` and will
  install into `.venv` if the explicit `--python` is omitted.
- **`--no-cov` is required** on the floor run too: `pytest.ini:13` `addopts` auto-applies `--cov`.
- **Record** the venv path, the resolved versions as read by
  `uv pip list --python <venv>/bin/python`, the exact command, and pass/fail — in the build report's
  `### Floor verification` subsection. An unrecorded floor run is not verifiable later.
- **Attribution caveat.** `tests/test_connection.py` carries **+82 lines** of a concurrent session's
  uncommitted work (`git diff --numstat` at this pass). If the floor run fails at *collection* — a
  3.11+-only syntax or API in someone else's lines — that is a concurrent-work blocker to report to
  Worker 0, **not** this item's failure and **not** something to fix. If it fails *in one of the two
  named rows*, that is R1c's and routes back through this item's loop; the fix is production code
  that works at the floor, never a raised floor and never a `pragma: no cover`.

### Decision 6 — Hot-path declaration

**Not hot-path. Declared explicitly rather than omitted** (`worker-1.md` `### Hot-path declaration`).

The item adds one `async def` test function and changes **no production line**: the diff against
`django_strawberry_framework/` is empty at the end of the pass (the two failability mutations are
transient and byte-proved reverted). The added code executes only under `pytest`, never per request,
per resolver, per row, per connection, or per outbound message. There is no serialization point, no
lock, no extra pass over a result set, and no per-item work inside a loop over a queryset — the
judgement is made on what the code runs inside, not on diff size. **No before/after number is owed**,
and Worker 2 writes `Not applicable; plan declares no hot path.` in the build report's
`### Hot-path budget` subsection.

### Decision 7 — Public surface

**Unchanged, and stated so Worker 3's `### Public-surface check` has an expectation to test
against.** `django_strawberry_framework/__init__.py` and its `__all__` are untouched by this item;
`git diff -- django_strawberry_framework/__init__.py` must be **empty**, and the file is **clean at
this planning pass** (`git status --porcelain` over it -> no entry), so an expectation of "empty" is
safe rather than confounded by concurrent work. `SyncMisuseError` is already exported (`__init__.py`
`:47`, `:151`); the test imports it from `django_strawberry_framework.types.relay` as the module
header already does (`:61`), adding no import and no export.

### Decision 8 — Boundary count and the split question

`worker-1.md` `### Boundary count is a split trigger` requires the count be written down and the
split question answered even when the diff is small.

**New boundaries this item adds: zero.** It adds no guard, cap, rejection path, or validation
branch — it *pins* a boundary that already ships. The two failability entries are
proofs of an existing boundary and a construction-time dispatch, not new ones. **No split.** One
test function in one file with one contract is not divisible, and splitting it would produce two
artifacts describing one assertion set.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. `tests/test_connection.py` is dirty under a
concurrent session, so **re-read the region before editing** — the anchors below will have moved.

1. Re-derive HEAD (`git rev-parse HEAD`) and re-read `tests/test_connection.py:1105-1130` to locate
   the sync sibling `test_sync_context_async_get_queryset_raises_sync_misuse` and the row after it,
   `test_connection_sync_resolver_returning_coroutine_raises_sync_misuse`.
2. `grep -c AsyncVisibilityAsyncExecNode tests/test_connection.py` -> must be **0**. Pick another
   free name if not.
3. Read `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` as the starting
   point. **Do not delete it** and do not delete anything under `docs/builder/temp-tests/`.
4. Insert the new row **between** those two functions, using `Edit` (a targeted insertion), never
   `Write` — `Write` would rewrite a file carrying another session's uncommitted work. Shape per
   Decisions 1-3:
   - `@pytest.mark.django_db(transaction=True)` + `async def
     test_async_execution_default_connection_async_get_queryset_raises_sync_misuse():`
   - Docstring: state the contract and name the mechanism by **symbol path**
     (`connection.py::_build_connection_resolver` commits the sync/async choice at construction, so
     a default field runs the sync pipeline under `await schema.execute` and an async
     `get_queryset` needs an `async def resolver=`). **No line numbers** (`AGENTS.md` rule 27), **no
     build-process vocabulary** — no worker/pass/round names, no review-doc names, no `bld-*`
     references. ASCII only. First line one sentence, under the line limit.
   - Body: local `from asgiref.sync import sync_to_async`; `await
     sync_to_async(services.seed_data)(1)`; the `async def get_queryset(cls, qs, info): return qs`
     hook; `_make_sidecar_node_type(<name>, get_queryset=get_queryset)`; `schema = await
     sync_to_async(_field_schema)(node_type)`; `result = await schema.execute("{ items { edges {
     node { id } } } }")`; the three assertions of Decision 2, in that order.
5. Tick the `### Dispatched findings checklist` boxes whose contracts landed, in the same build
   report that lands them.
6. Failability proofs, Decision 4 — entry 1 fully (mutate, run, restore, `cmp`) before entry 2 is
   started. Record every field `BUILD.md` `### What gets recorded` requires: boundary by
   symbol-qualified path, exact mutation, scope as run, **pre-mutation state of that scope**,
   failing node ids **listed** (never a bare count), collection/setup errors **separately** (a valid
   count requires 0), and the revert proved by byte-comparison. Plus the two `shasum` readings per
   entry that Decision 4's concurrent-writer clause requires.
7. Floor verification, Decision 5. Record the venv path, resolved versions, command, and result.
8. Lint, in this order and **read-only first** because the file carries concurrent work:
   - `uv run ruff format --check tests/test_connection.py` and `uv run ruff check
     tests/test_connection.py`. Inspect what they want to change.
   - Apply the write-mode runs (`uv run ruff format tests/test_connection.py`, `uv run ruff check
     --fix tests/test_connection.py`) **only if the changes are confined to the added row**. If
     either tool wants to rewrite lines outside it, do **not** apply it — hand-fix the added row and
     **report** the pre-existing drift. Never `.` as the target.
   - `uv run python scripts/check_trailing_commas.py --check tests/test_connection.py` first (it
     auto-fixes by default, which on a concurrent-dirty file is a write you did not intend); apply
     the fix only if it is confined to the added row.
9. `git status --short` after the lint runs. Every modified path must be slice-intended and appear
   in `### Files touched`. Anything else is a **stop-and-report**, never a revert.
10. Focused run: `uv run pytest tests/test_connection.py --no-cov`. **No `--cov*` flag in any pass**
    — `--no-cov` is the only permitted coverage-shaped flag, because `pytest.ini:13` `addopts`
    auto-applies `--cov`.
11. Set `Status: built` and write `### Notes for Worker 1 (spec reconciliation)` — including, if the
    build surfaces one, any claim in `spec-009` or its rationale that this row's measured behavior
    falsifies. R1 and R1b both closed `final-accepted`, so a fresh falsification is a real finding,
    not bookkeeping.

### Test additions / updates

- **`tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`**
  — the item's whole deliverable. Pins that a **default** `DjangoConnectionField` over a type
  declaring `async def get_queryset` surfaces `SyncMisuseError` as a top-level GraphQL error under
  `await schema.execute`, with `result.data is None`. Assertion shape fixed by Decision 2.
- **No existing test is edited.** The sync sibling stays exactly as it is; it is the twin, not a
  duplicate. No test is deleted.
- **Temp tests.** `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is the
  starting point and is **not deleted by any pass of this item** (dispatch instruction). Worker 3
  records its disposition under `### Temp test verification` as *superseded by the permanent row;
  retained per the cycle's do-not-delete instruction; clears with the cycle's scratch*. Worker 3 may
  add further temp tests under `docs/builder/temp-tests/r1c/` if it needs to demonstrate that an
  assertion is non-distinguishing; the failability manifest also lives under that directory.
- **No new test file, no new fixture, no new conftest entry.**

### Static inspection

`scripts/review_inspect.py` was run this pass on the target file —
`uv run python scripts/review_inspect.py tests/test_connection.py --output-dir docs/shadow`, exit 0,
emitting `docs/shadow/tests__test_connection.overview.md` and `.stripped.py`. It is what mechanically
cross-checked the six function-local `sync_to_async` import sites cited in `### DRY analysis` (the
rule behind them was established by the AST walk in `### Decision 3`, not by this helper), and
reported 38 imports, 144 symbols, 4 control-flow hotspots, 28 repeated string literals. Worker 3 owes its
own run only if this item's diff crosses that role's thresholds; a single added test function in a
test file does not add 50+ lines of new logic, so a recorded skip with that reason is acceptable.

### Implementation discretion items

Assessed and decided to be Worker 2's, per `ARTIFACT.md`:

- The throwaway `Meta.name` string, subject to the uniqueness check in step 2.
- Exact docstring wording, within Decision 1/2's constraints (symbol paths only, ASCII, no
  process vocabulary, first line inside the line limit).
- Whether `assert result.data is None` carries a short trailing comment naming what it rules out.
- Argument explosion inside the `_make_sidecar_node_type(...)` call and blank-line placement, so
  long as `scripts/check_trailing_commas.py --check` is clean on the added lines.
- The order of the two failability entries' *manifest* fields, and whether both entries share one
  manifest file or two — the **order of execution** (entry 1 fully reverted before entry 2) is not
  discretionary.

Nothing architectural is delegated here.

### Dispatched findings checklist

One box per contract Worker 2 must land. Worker 2 ticks `- [x]` only a box whose contract actually
landed in its diff, in the same build report; a deferral is stated in the build report rather than
ticked. Worker 1 audits every tick at final verification.

- [x] A permanent row exists at `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`, placed immediately after `test_sync_context_async_get_queryset_raises_sync_misuse`.
- [x] The row drives a **default** `DjangoConnectionField` — `_field_schema(node_type)` with **no** `resolver=` argument — over a type whose `get_queryset` is `async def`, under `await schema.execute` with the minimal query `{ items { edges { node { id } } } }`.
- [x] The assertions are the three of `### Decision 2`, in order: `result.errors is not None`; `any(isinstance(err.original_error, SyncMisuseError) for err in result.errors)`; `result.data is None`. No `pytest.raises`, no message-substring-only assertion, no base-class `ConfigurationError` assertion.
- [x] The row seeds first — `await sync_to_async(services.seed_data)(1)` — per `AGENTS.md` rule 8, and carries `@pytest.mark.django_db(transaction=True)`.
- [x] The row adds **no** module-level import; its only import is the function-local `from asgiref.sync import sync_to_async`, and it builds the schema via `await sync_to_async(_field_schema)(node_type)` per the six-of-six rule for DB-touching async rows in `### Decision 3`.
- [x] Failability entry 1 recorded in full for `utils/querysets.py::apply_type_visibility_sync` #"result = reject_async_in_sync_context(" — anchor count 1 verified before the copy, mutation, scope as run, pre-mutation state, failing node ids **listed**, collection/setup errors separately (0), revert proved by `cmp`, plus the two `shasum` readings.
- [x] Failability entry 2 recorded in full for `connection.py::_build_connection_resolver` #"if resolver is None:" — and it states explicitly that the new row is among the failures **and** that its failure mode is "the query succeeded" (`errors is None` / `data` populated).
- [x] Both mutations reverted before the `Status:` transition, each proved by byte-comparison against an out-of-repo pre-mutation copy; no `git stash` / `checkout` / `restore` / `worktree` used anywhere.
- [x] Floor verification run and recorded by **this pass**: isolated venv outside the repo, the floor versions read from `BUILD.md` `## Floor verification`, resolved versions captured via `uv pip list --python <venv>/bin/python`, the two node ids of `### Decision 5` run with `--no-cov`, pass/fail recorded.
- [x] `### Hot-path budget` states `Not applicable; plan declares no hot path.`
- [x] `git diff -- django_strawberry_framework/__init__.py` is empty at the end of the pass, and `git diff -- django_strawberry_framework/` shows **no** net change from this item (both mutations reverted).
- [x] Ruff and `scripts/check_trailing_commas.py` run **scoped to `tests/test_connection.py`** (never `.`), read-only first, and any change the tools want outside the added row is reported rather than applied.
- [x] Focused run `uv run pytest tests/test_connection.py --no-cov` recorded, with no `--cov*` flag used in any pass.
- [x] Nothing under `docs/builder/temp-tests/` deleted; no concurrent file edited, reverted, or checked out; nothing committed; no branch created.

### Standing constraints inherited by the builder

Repeated here because they bind every pass on this item, not only the planning one:

- **Writable set for the build pass: `tests/test_connection.py`, this artifact, and the failability
  scratch under `docs/builder/temp-tests/r1c/`.** Plus the two production files **transiently**, for
  the two failability mutations only, each reverted and byte-proved inside the same pass.
- The tree is heavily dirty across four concurrent cycles, a REVIEW cycle, a DRY cycle, and a
  package-source session, and HEAD moves several times per pass. **Never edit, revert, or
  `git checkout` any concurrent file**; re-derive HEAD rather than trusting a hash written down
  anywhere.
- **Do not edit** the spec, the rationale, the build plan, or any source or test file other than
  `tests/test_connection.py`.
- `uv run ruff format` / `ruff check --fix` **scoped to the files the pass touches, never `.`**.
- **No `pytest` with any `--cov*` flag** in any pass; `--no-cov` is the only permitted
  coverage-shaped flag.
- `AGENTS.md` rule 17 — line length 100, trailing-comma explode-at-threshold layout, ASCII-only `.py`
  source; `AGENTS.md` rule 27 — symbol-qualified source refs in code, never `path:NN`.
- **Only the maintainer commits.** Never commit, never branch, never amend.

### Notes for Worker 1 (spec reconciliation)

Nothing owed at planning. Two things to weigh at final verification:

- Whether the measured behavior of the two failability entries confirms `spec-009:417`'s corrected
  wording (R1's change 42) and its rationale twin. Entry 2 is, in effect, an executable proof of that
  correction; if the measurement disagrees with the corrected clause, that is a spec finding and R1's
  `final-accepted` region gets re-opened on **falsity**, not resemblance.
- Whether `tests/test_connection.py`'s module docstring reference to `docs/spec-030-connection_field-0_0_9.md`
  is a stale path (the spec archive moved `docs/spec-*` to `docs/SPECS/`). **Out of this item's
  writable scope** — record for the maintainer, do not fix here.

---

## Build report (Worker 2)

Build pass run 2026-08-16 by a fresh Worker 2 invocation. HEAD re-derived at the start of the pass
and again at its end: **`6f8bf818`** both times (unchanged across this pass, though four concurrent
cycles are writing the tree). The rationale companion was **not** read, per the required-reading
matrix.

### Files touched

Grounded in `git status --short`, not memory. Only the first is tracked; the rest are gitignored
scratch under paths `.gitignore` already lists.

- `tests/test_connection.py` — **the item's whole deliverable.** One added `async def` row,
  `test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`, inserted between
  `test_sync_context_async_get_queryset_raises_sync_misuse` and
  `test_connection_sync_resolver_returning_coroutine_raises_sync_misuse`. **+31 lines, 0 deletions,
  0 edits to any existing row.** The file is also carrying a concurrent session's uncommitted work
  (see `### Validation run`), so its `M` status is not this pass's alone.
- `docs/builder/bld-009-r1c-async_syncmisuse_test_row.md` — this build report appended, `Status:`
  set to `built`, and all 14 `### Dispatched findings checklist` boxes ticked. The
  `## Plan (Worker 1)` prose is untouched apart from those box markers.
- `docs/builder/worker-memory/spec-009-worker-2.md` — created (it did not exist) and one entry
  appended. Gitignored.
- `docs/builder/temp-tests/r1c/proofs.json` — the failability manifest, at the plan's named home.
  Gitignored.
- `docs/builder/temp-tests/r1c/proofs-report.md` — `scripts/prove_failability.py --output`'s emitted
  record, the measured source for `### Failability proofs` below. Gitignored.

**Nothing under `docs/builder/temp-tests/` was deleted**; `docs/builder/temp-tests/r1/test_async_execution_default_connection.py`
is untouched and still on disk. No package source carries any net change from this pass (the two
failability mutations are byte-proved reverted, below). No spec, rationale, build plan, kanban DB,
`KANBAN.md`, `docs/GLOSSARY.md`, or other test file was edited. Nothing committed; no branch created;
no `git stash` / `checkout` / `restore` / `worktree` used anywhere in this pass.

### Tests added or updated

- **`tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`**
  — pins that a **default** `DjangoConnectionField` (`_field_schema(node_type)`, **no** `resolver=`
  argument) over a type declaring `async def get_queryset` surfaces `SyncMisuseError` as a top-level
  GraphQL error under `await schema.execute`, with `result.data is None`. Query is the minimal
  `{ items { edges { node { id } } } }` — no `filter:`, no `orderBy:`, no `totalCount`, no
  `first`/`last` — so it can only take the path it claims to test. Carries
  `@pytest.mark.django_db(transaction=True)`, seeds first via
  `await sync_to_async(services.seed_data)(1)`, and builds the schema via
  `await sync_to_async(_field_schema)(node_type)`, per `### Decision 3`'s six-of-six rule for
  DB-touching async rows. Its only import is the function-local
  `from asgiref.sync import sync_to_async`; **no module-level import was added.** Throwaway
  `Meta.name` is `AsyncVisibilityAsyncExecNode`, verified free before writing
  (`grep -c AsyncVisibilityAsyncExecNode tests/test_connection.py` -> **0**).
- The three assertions are `### Decision 2`'s, in order: `result.errors is not None`;
  `any(isinstance(err.original_error, SyncMisuseError) for err in result.errors)`;
  `result.data is None`. No `pytest.raises`, no message-substring assertion, no base-class
  `ConfigurationError` assertion.
- **No existing test edited, none deleted.** The sync sibling stands exactly as it was.

### Validation run

Read-only first, then write-mode, all scoped to the one file — never `.`.

- `uv run ruff format --check tests/test_connection.py` — **pass** (`1 file already formatted`).
- `uv run ruff check tests/test_connection.py` — **pass** (`All checks passed!`).
- `uv run ruff format tests/test_connection.py` — **pass**, `1 file left unchanged`. File `shasum`
  `8a66cf29…` identical before and after, so the write-mode run touched nothing outside the added
  row (it touched nothing at all).
- `uv run ruff check --fix tests/test_connection.py` — **pass**, `All checks passed!`, same `shasum`.
- `uv run python scripts/check_trailing_commas.py --check tests/test_connection.py` — **fails on one
  line, and that line is not this pass's.** Reported: `tests/test_connection.py:1062: should explode
  (>= threshold, no trailing comma)`, which is `async def __call__(self, prefix, root, info):` inside
  `_Resolver` in a **concurrent session's uncommitted row**. Verified not mine two ways: the added
  row spans lines 1127-1155, and `git show HEAD:tests/test_connection.py` (read into a scratch path
  outside the repo) does **not** contain that line, so it arrived in the concurrent session's +82
  lines rather than existing at HEAD. **Reported, not fixed** — the script auto-fixes by default and
  applying it would rewrite another session's line. The added row itself is clean: no violation is
  reported anywhere in 1127-1155.
- **Line length**, measured rather than eyeballed: the added row's longest line is **90** characters
  (the `async def` signature and the docstring's first line, both 90), inside the 100 limit; ASCII
  only.
- `git status --short` after both ruff invocations — the tree carries **~60 modified test files, ~55
  modified package files, `KANBAN.md` / `KANBAN.html`, and a dozen untracked `docs/builder/` paths**,
  all four concurrent cycles' and the package-source session's work. **The only R1c-intended path in
  it is `tests/test_connection.py`**, which appears in `### Files touched`. Everything else is
  stop-and-report material rather than something to revert, and this bullet is the report: none of it
  was touched, reverted, or checked out.
- Focused run: `uv run pytest tests/test_connection.py --no-cov` — **69 passed** (68 before this
  pass). The new row was confirmed collected and executed, not silently skipped as an unawaited
  coroutine: `uv run pytest "tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse" --no-cov -p no:randomly -v` -> **1 passed**.
- **No `--cov*` flag was used in any command of this pass.** `--no-cov` is the only coverage-shaped
  flag that appears, and it is required because `pytest.ini`'s `addopts` auto-applies `--cov`.

### Failability proofs

Both entries were performed with `scripts/prove_failability.py` against
`docs/builder/temp-tests/r1c/proofs.json`, which runs anchor check -> pre-mutation baseline ->
out-of-repo pristine copy -> mutation -> focused run -> restore -> byte comparison, in that order,
one boundary live at a time. Final run exit code **0** (every entry proved, none weakly pinned, no
collection/setup error). Emitted record: `docs/builder/temp-tests/r1c/proofs-report.md`. Scratch root
is outside the repository. `git` was never invoked as part of any mutation, restore, or proof.

**Anchor counts verified before any copy was taken**, exactly as `### Decision 4` requires:
`grep -c 'result = reject_async_in_sync_context(' django_strawberry_framework/utils/querysets.py`
-> **1**; `grep -c 'if resolver is None:' django_strawberry_framework/connection.py` -> **1**. A
`--check-anchors-only` pass then re-confirmed both match exactly once before the first mutation.

**`shasum` readings, per `### Decision 4`'s concurrent-writer clause** — taken immediately before the
mutating run and immediately after the restore, for each target:

| Target | Before mutation | After restore |
|---|---|---|
| `django_strawberry_framework/utils/querysets.py` | `4cd72adc39efafe734d2cef8db288c663b4b5cdb` | `4cd72adc39efafe734d2cef8db288c663b4b5cdb` |
| `django_strawberry_framework/connection.py` | `e410c8682a7707c646b8b49984a1b170f7a5699a` | `e410c8682a7707c646b8b49984a1b170f7a5699a` |

Both identical, so no concurrent write landed inside either mutation window and no third-party bytes
were clobbered by a restore. The `cp`-restore-on-mismatch abort was therefore never reached. No
`ACTIVE-MUTATION.json` marker survives in the scratch root.

**Scope as run, for both entries (kept identical so the node-id sets are differenced, not the
counts):**

```
uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE \
    tests/test_connection.py -n0 -p no:randomly -W ignore::RuntimeWarning
```

The scope carries three additions to the plan's `uv run pytest tests/test_connection.py --no-cov`,
each forced by a measurement rather than chosen — see `### Notes for Worker 1 (spec reconciliation)`
for the drift record and `### Notes for Worker 3` for how to reproduce it. In short: `-n0
-p no:randomly` make the run deterministic, and `-W ignore::RuntimeWarning` neutralizes a
**mutation artifact** — under entry 2 every `execute_sync` row against a default field receives an
awaitable, Strawberry discards it, and the resulting `RuntimeWarning: coroutine ... was never
awaited` lands as a warnings-as-errors **teardown error on a different neighbouring row each run**
(observed on three different node ids across four runs). That is a collection/setup error, which
`BUILD.md` `### What gets recorded` says is not a valid count at all. Suppressing that one warning
class removes the artifact without touching a single assertion, and it can only ever **lower** a
count, never inflate one — which is the direction the acceptance rule cares about. Both entries
finish at **0 collection/setup errors**.

**Entry 1 — the guard `### Maintainer decision 5` names.**

- `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` #"result = reject_async_in_sync_context(" — **mutation applied:** the whole
  `result = reject_async_in_sync_context(result, owner=..., method="get_queryset", context="resolver", recourse=async_recourse)`
  call **deleted outright**, so the coroutine returned by `type_cls.get_queryset(queryset, info)`
  flows straight into `_normalized_visibility_result` with no sync-context guard. That **removes**
  the boundary rather than perturbing code near it; **scope as run:** the invocation above;
  **pre-mutation state of that scope:** `69 passed`, pytest exit code 0 — green, so 0 pre-existing
  failing rows were differenced out; **failing node ids** (mutant summary `2 failed, 67 passed`,
  exit code 1):
  - `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse`
  - `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`

  **collection/setup errors: 0** (a valid count); **revert proved by byte-comparison:**
  `filecmp.cmp(shallow=False) True; sha256 6fb44ccdcb9a462d… == 6fb44ccdcb9a462d…` against the
  out-of-repo pre-mutation copy, plus the `shasum` pair in the table above.

  **Reading.** Exactly the two rows `### Decision 4` pre-decided, and the sibling failing alongside
  the new row is expected and correct: both drive `apply_type_visibility_sync`, both assert the
  `SyncMisuseError` **subclass**, and with the guard gone the coroutine is rejected downstream as a
  plain `ConfigurationError`, which the `isinstance` assertion refuses. **2 rows clears the
  weakly-pinned threshold** (`BUILD.md` `### Acceptance rule`: 0 or 1 is `revision-needed`). Neither
  of the plan's two defect branches was hit — it is not "only the new row" (which would have meant a
  skipped or collection-errored sibling) and not "only the sibling" (which would have meant the new
  row does not pin this boundary). The count sits inside Worker 3's mandatory independent re-run
  floor (<= 3 rows), so Worker 3 owes a re-run of this entry at the recorded scope.

**Entry 2 — the construction-time pipeline choice, which is what makes the new row non-redundant.**

- `django_strawberry_framework/connection.py::_build_connection_resolver` #"if resolver is None:" —
  **mutation applied:** in that branch alone, `def _resolve(...)` became `async def _resolve(...)`
  and `return _pipeline_sync(...)` became `return await _pipeline_async(...)`; every other branch,
  argument, and line left byte-identical. This gives the default field precisely the async pipeline
  the contract says construction denies it; **scope as run:** the invocation above, identical to
  entry 1's; **pre-mutation state of that scope:** `69 passed`, pytest exit code 0 — green, 0
  pre-existing failing rows differenced out; **failing node ids** (mutant summary
  `11 failed, 58 passed`, exit code 1):
  - `tests/test_connection.py::test_connection_resolver_composition_order`
  - `tests/test_connection.py::test_relay_max_results_cap`
  - `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse`
  - `tests/test_connection.py::test_root_connection_field_queryset_is_planned`
  - `tests/test_connection.py::test_root_connection_field_queryset_prefetches_node_many_relation`
  - `tests/test_connection.py::test_nested_connection_unplanned_raises_under_strictness`
  - `tests/test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count`
  - `tests/test_connection.py::test_connection_hostile_hook_narrows_edges_and_total_count_sync`
  - `tests/test_connection.py::test_connection_instance_shadowed_all_hook_is_sealed`
  - `tests/test_connection.py::test_connection_query_chain_shadow_hook_is_sealed`
  - `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`

  **collection/setup errors: 0** (a valid count); **revert proved by byte-comparison:**
  `filecmp.cmp(shallow=False) True; sha256 8db2ac5eb1bca4e5… == 8db2ac5eb1bca4e5…` against the
  out-of-repo pre-mutation copy, plus the `shasum` pair in the table above.

  **The narrow question this entry exists to answer, answered explicitly.** The new row
  **`test_async_execution_default_connection_async_get_queryset_raises_sync_misuse` is among the
  failures** (last id in the list above), and **its failure mode is "the query succeeded"** — not a
  different error, not a changed message. Captured verbatim at the recorded scope with `--tb=long`
  inside its own bracketed mutation window:

  ```
  >       assert result.errors is not None
  E       AssertionError: assert None is not None
  E        +  where None = ExecutionResult(data={'items': {'edges': [{'node': {'id': 'cHJvZHVjdHMuY2F0ZWdvcnk6NzY='}}, …]}}, errors=None, extensions={}).errors
  ```

  The seeded row was served. That is the evidence that this row, and nothing else in the suite, pins
  "async execution does not get a different pipeline": the sync sibling also fails under this
  mutation, but it fails on `execute_sync` meeting an awaitable, not on a successful async query.
  Entry 1 alone could not have distinguished the two rows; this entry does.

**Both entries, in order, one at a time.** Entry 1 was fully reverted and its revert proved before
entry 2's anchor was located, enforced by the tool's per-entry `finally` restore. No mutation was
live across the `Status:` transition, and the tree handed to Worker 3 carries neither.

### Hot-path budget

Not applicable; plan declares no hot path.

Confirmed against the diff rather than assumed: the pass adds one `async def` test function and
changes **no production line** — `git diff --stat -- django_strawberry_framework/__init__.py` is
empty, and both failability targets `cmp` byte-identical to their pre-mutation copies with matching
`shasum` readings, so this item's net change to `django_strawberry_framework/` is nil. The added code
runs only under `pytest`, never per request, resolver, row, connection, or outbound message.

### Floor verification

Owned by **this pass**, per `### Decision 5` and `### Maintainer decision 5`, which amend the build
plan's blanket `Floor-verification scope: none` for R1c alone. Floor versions taken from `BUILD.md`
`## Floor verification` (re-read this pass; it is the single canonical statement), not from memory or
any other document.

- **Scratch venv path (outside the repo):**
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/fc7d0b3d-4cfd-4ed0-a153-22f1402f6dfd/scratchpad/dsf-floor`
- **Built per `### How to build the floor venv`, verbatim**, every install carrying an explicit
  `--python`:
  - `uv venv <venv> --python 3.10` -> `Using CPython 3.10.19`
  - `uv pip install --python <venv>/bin/python -e . --group dev`
  - `uv pip install --python <venv>/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'`
    -> downgraded `django 5.2.17 -> 5.2.16` and `strawberry-graphql 0.324.0 -> 0.316.0`
- **Resolved versions, as read by `uv pip list --python <venv>/bin/python`:** `django 5.2.16`,
  `strawberry-graphql 0.316.0`, `asgiref 3.12.1`, `graphql-core 3.2.11`, `django-filter 26.1`,
  `channels 4.3.2`, `djangorestframework 3.18.0`, `pytest 9.1.1`, `pytest-django 4.14.0`,
  `pytest-asyncio 1.4.0`; interpreter `Python 3.10.19`.
- **Focused scope run at the floor** — the two node ids of `### Decision 5` and nothing wider:

  ```shell
  <venv>/bin/python -m pytest \
      "tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse" \
      "tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse" --no-cov
  ```

- **Result: PASS — `2 passed in 6.23s`.** Collection succeeded, so `### Decision 5`'s attribution
  caveat was never triggered: no 3.11+-only syntax or API in the concurrent session's lines blocked
  the floor run, and neither named row failed. Both execution colors reach the same guard on the
  oldest supported stack.
- **The shared `.venv` was never mutated.** Verified after the floor build: `uv pip list` in the
  shared environment still reports `django 6.1` / `strawberry-graphql 0.323.2` on `Python 3.14.2` —
  the floor's 5.2.16 / 0.316.0 / 3.10.19 went nowhere near it. Every install carried
  `--python <venv>/bin/python`, which is what keeps `uv pip install` from ignoring
  `UV_PROJECT_ENVIRONMENT` and landing in `.venv`.
- `--no-cov` was carried on the floor run too, since `pytest.ini`'s `addopts` auto-applies `--cov`.

### Implementation notes

Only the choices `### Implementation discretion items` delegated, plus the small shapes the plan left
open. Nothing architectural was decided here.

- **Throwaway `Meta.name` = `AsyncVisibilityAsyncExecNode`**, the plan's suggestion, verified free
  (`grep -c` -> 0) before writing. It pairs by eye with the sibling's `AsyncVisibilitySyncNode`.
- **Docstring shape.** First line is one sentence at 90 characters. The body names the mechanism by
  symbol path only — `connection.py::_build_connection_resolver`,
  `utils/querysets.py::apply_type_visibility_sync`,
  `utils/querysets.py::reject_async_in_sync_context` — with **no line numbers** (`AGENTS.md` rule 27)
  and no build-process vocabulary. It closes on the consumer recourse the module itself documents
  (supply an `async def` `resolver=`), so a reader who trips this error learns the fix from the test.
  ASCII only.
- **`assert result.data is None` carries a trailing comment** — `# an async pipeline would have
  served the seeded row` — taking the discretion item's offer. It is the one assertion whose purpose
  is not self-evident from its own text, and entry 2's measured failure mode is literally that
  sentence.
- **Argument layout.** `_make_sidecar_node_type("AsyncVisibilityAsyncExecNode", get_queryset=get_queryset,)`
  is exploded one-argument-per-line with a trailing comma, byte-matching the sibling's call layout;
  `scripts/check_trailing_commas.py --check` reports nothing anywhere in the added row.
- **Blank line before the assertion block**, following the async precedent
  `test_connection_hostile_hook_narrows_edges_and_total_count_async` rather than the sync sibling
  (which runs assertions straight on from the `execute_sync` call). The sibling's tighter shape reads
  fine at four lines; this row's setup is longer.
- **Both failability entries share one manifest**, `docs/builder/temp-tests/r1c/proofs.json` — the
  plan's named home and its stated discretion. Sharing one file is what let both entries carry a
  byte-identical `scope`, which is the property that makes their node-id sets differenceable. The
  **order of execution** (entry 1 fully reverted before entry 2) was not treated as discretionary and
  is enforced by the tool.
- **The temp body's two departures, both resolved as the plan directed.** Its cross-module
  `from tests.test_connection import _field_schema, _make_sidecar_node_type` disappears with
  same-file placement, and its mixed fixture shape (`django_db(transaction=True)` marker with a
  direct `_field_schema(...)` call — the one mixed shape in either class) became the six-of-six
  DB-touching shape: seed wrapped, builder wrapped. The temp file itself is left on disk untouched.

### Notes for Worker 3

- **Reproducing the proofs.** `uv run python scripts/prove_failability.py docs/builder/temp-tests/r1c/proofs.json`
  re-runs both entries end to end; `--only 1` / `--only 2` narrows (the emitted block is then
  labelled PARTIAL RECORD, which is expected for a subset re-run). The manifest already carries the
  exact anchors, mutations, and the scope recorded above, so an independent re-run measures the same
  scope by construction. Entry 1 is **inside the mandatory re-run floor at 2 rows**; entry 2 at 11
  rows is above it.
- **Expect entry 2's row set to be scheduler-stable only at `-n0`.** Under the repo's default `-n
  auto` the mutant's leaked-coroutine warning becomes a teardown ERROR on a *different* node each
  run (`test_async_consumer_resolver_iterable_with_total_count_selected_raises`,
  `test_connection_async_pipeline_applies_filter_and_order` and `test_attach_count_async_awaits_before_guard_raises`
  were each hit once across four runs). If a re-run at the recorded scope reports a
  collection/setup error, check first that all of `-n0 -p no:randomly -W ignore::RuntimeWarning`
  were carried — dropping any one reintroduces the artifact.
- **Entry 1's row set is narrower than an early measurement suggested, deliberately.** At
  `-n0 -p no:randomly` without the warning filter it read 4 rows (adding
  `test_async_consumer_resolver_iterable_with_total_count_selected_raises` and
  `test_connection_type_for_generates_total_count_for_direct_relay_inheritance`); those two are
  warning-artifact rows, and the filter removes them. 2 rows is the conservative number and still
  clears the acceptance rule. If you prefer the unfiltered scope, the two extra rows are what you
  should see.
- **No shadow file was used this pass.** `scripts/review_inspect.py` was not re-run: Worker 1 ran it
  during planning (exit 0, emitting `docs/shadow/tests__test_connection.overview.md`) and this pass
  added no logic that would change its output. Per `BUILD.md` `### When to run the helper during
  build`, Worker 3's threshold for a test file is 50+ lines of new logic; this diff is 31 lines of
  test in a test file, so a recorded skip with that reason is available to you.
- **`tests/test_connection.py` is concurrent-dirty.** `git show HEAD:tests/test_connection.py` into a
  scratch path outside the repo is the read-only way to separate this pass's 31 lines from the
  session's ~82. Do not `git checkout` the file.
- **The one lint failure is not mine** — `check_trailing_commas.py` line 1062, inside a concurrent
  row, evidence in `### Validation run`. Please do not fix it here either; it auto-fixes by default,
  which on this file is a write into someone else's work.
- **The public surface is unchanged**, so `### Public-surface check` has a clean expectation:
  `git diff -- django_strawberry_framework/__init__.py` is empty. `SyncMisuseError` was already
  exported and already imported at the target module's header; the row adds no import and no export.

### Notes for Worker 1 (spec reconciliation)

- **Drift, small and mechanically obvious — the failability scope carries three flags the plan did
  not name.** `### Decision 4` fixes the focused scope as `uv run pytest tests/test_connection.py
  --no-cov`; both entries actually ran at `tests/test_connection.py -n0 -p no:randomly -W
  ignore::RuntimeWarning` (plus the tool's own fixed flags). **Recommended replacement**, in
  `### Decision 4`, for both entries' `**Focused scope:**` line: `uv run pytest
  tests/test_connection.py -n0 -p no:randomly -W ignore::RuntimeWarning --no-cov` — with the
  sentence *"the determinism flags and the `RuntimeWarning` filter are required, not cosmetic: under
  entry 2's mutation every `execute_sync` row against a default field receives an awaitable that
  Strawberry discards, and the resulting unawaited-coroutine warning lands as a warnings-as-errors
  teardown error on a different neighbouring row each run, which `BUILD.md` grades as no valid count
  at all."* The plan's expectation that the two scopes stay **identical to each other** is preserved
  exactly. This is evaluable from the manifest and the report alone, so it is recorded rather than
  paused on.
- **Entry 2 confirms `spec-009:417`'s corrected wording rather than falsifying it.** The plan's own
  final-verification question: with the default branch converted to `async def _resolve` + `await
  _pipeline_async`, the new row's query **succeeds** (`errors=None`, seeded row served), and with the
  branch as shipped it raises `SyncMisuseError`. That is an executable proof that the sync/async
  pipeline choice for a default `DjangoConnectionField` is made at **construction**, not per
  execution. No spec finding; R1's `final-accepted` region does not re-open on this.
- **Stale spec path in the target module's docstring, unchanged and out of scope.**
  `tests/test_connection.py`'s module docstring still reads `Spec: ``docs/spec-030-connection_field-0_0_9.md```
  while the archive moved `docs/spec-*` to `docs/SPECS/`. The plan already flagged it as outside this
  item's writable scope, and this pass did not touch it. **Recommended handling:** record it for the
  maintainer rather than folding it into R1c — the fix is a one-line docstring edit in a file two
  sessions are writing, and it belongs to whichever cycle owns the archive's inbound references (R4's
  cross-reference audit is the natural home).
- **No plan-vs-implementation pause was taken.** Nothing structural in the plan turned out wrong: the
  placement, the assertion shape, the fixture rule, both failability boundaries, and the floor
  declaration all held as written.

---

## Review (Worker 3)

Review pass run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. HEAD re-derived at the start of the pass:
**`6f8bf818e9b1bc45059017c17fc346a3daca0b8f`**. The rationale companion and the plan were read; no
other worker's memory file was opened.

### Independent failability re-run — mutation recorded BEFORE it is made

`worker-3.md` "Reading is necessary, not sufficient" puts **entry 1 (2 rows) inside the mandatory
re-run floor**. Recorded here ahead of the mutation, per the same section:

- **Boundary to be re-mutated:** `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`
  #"result = reject_async_in_sync_context(".
- **Mutation to be applied:** delete the whole `result = reject_async_in_sync_context(result,
  owner=..., method="get_queryset", context="resolver", recourse=async_recourse)` call, so the
  coroutine returned by `type_cls.get_queryset` flows straight into `_normalized_visibility_result`
  with no sync-context guard. Byte-identical to Worker 2's entry 1 mutation.
- **Scope:** Worker 2's recorded scope, byte-identical — `tests/test_connection.py -n0 -p no:randomly
  -W ignore::RuntimeWarning` — so the node-id **sets** are comparable rather than the counts. A
  second, **unfiltered** run at `tests/test_connection.py -n0 -p no:randomly` is also taken, to grade
  the `-W` scope drift of `### Notes for Worker 1` rather than accept its account.
- **Independence:** driven from a Worker-3-authored manifest at
  `docs/builder/temp-tests/r1c/w3-reproof.json`, not Worker 2's `proofs.json`; scratch root outside
  the repository; `scripts/prove_failability.py` enforces anchor-check -> baseline -> copy -> mutate
  -> run -> restore -> byte-compare order.
- **Revert:** proved by byte-comparison inside this same pass. No `git stash` / `checkout` /
  `restore` / `worktree` at any point.

Results are recorded under `### Failability proofs` below.

**Second mutation, recorded before it is made.** Entry 2 sits **above** the mandatory floor (11
rows), so this re-run is discretionary. It is taken anyway because entry 2 is the only evidence that
the new row is not a duplicate of its sync sibling — the single load-bearing claim of the whole item
— and a discretionary re-run of exactly that claim is what `worker-3.md` "above that floor, re-run
anything else you have grounds to distrust" is for.

- **Boundary:** `django_strawberry_framework/connection.py::_build_connection_resolver`
  #"if resolver is None:".
- **Mutation:** in that branch alone, `def _resolve(...)` -> `async def _resolve(...)` and
  `return _pipeline_sync(...)` -> `return await _pipeline_async(...)`; every other branch byte-identical.
  Byte-identical to Worker 2's entry 2 mutation.
- **Scope:** Worker 2's recorded scope, byte-identical.
- **Revert:** proved by byte-comparison inside this same pass.

**Third mutation, recorded before it is made.** Entry 2's node-id set alone does not verify the one
claim the item rests on — that the new row's failure mode under that mutation is *"the query
succeeded"* rather than some other error. `scripts/prove_failability.py` fixes `--tb=no`, so this one
window is run through `BUILD.md`'s fenced fallback loop instead, in its stated order.

- **Boundary / mutation:** identical to the entry-2 mutation above.
- **Scope:** the single node id
  `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`,
  with `--tb=long` so the assertion and the `ExecutionResult` are visible. A single-node scope is used
  here only to read a failure mode already counted at the recorded scope; it is not a row count.
- **Revert:** `cp` from the out-of-repo pre-mutation copy, proved by `cmp`.

### High:

None.

### Medium:

None.

### Low:

#### `### Decision 1` ground 2 is false, and ground 1 is overstated — the placement outcome is right, its stated rationale is not

`### Decision 1` discharges `AGENTS.md` rule 10 on three grounds and asserts "**Grounds 1 and 2 are
each independently sufficient.**" Ground 2 reads: *"The live transport is sync.
`examples/fakeshop/test_query/` exercises `/graphql/` over `django.test.Client` ... The
distinguishing execution color is not available there."*

**That is disprovable by one grep.** The live tier already mounts the async view on a real event
loop, over probe schemas built from fakeshop's own types:

```examples/fakeshop/test_query/test_error_policy_api.py:192
def _probe_async_view(**schema_kwargs):
    """The async twin of ``_probe_view``, so parity is proven on a real event loop."""

    async def view(request, *args, **kwargs):
        built = AsyncDjangoGraphQLView.as_view(schema=_probe_schema(**schema_kwargs))
        return await built(request, *args, **kwargs)
```

`examples/fakeshop/test_query/test_resource_policy_api.py` (`:129`) and
`examples/fakeshop/test_query/test_transport_api.py` (`:239`, `:381`, `:398`) carry the same mount,
and `views.py::AsyncDjangoGraphQLView` states the consequence itself — *"Django dispatches it on the
event loop rather than an executor thread. Resolvers then run in async context."* The async
execution colour **is** available in the live tier.

Ground 1 is overstated for the same reason: "the live tier cannot host the fixture without
destroying itself" holds only for fakeshop's **shipped** types. A probe schema is precisely the
tier's mechanism for hosting a fixture the shipped schema cannot, and
`test_library_api.py`'s flag-gated `FAKESHOP_TEST_LOAN_CONNECTION` connection is a shipped precedent
for adding test-scoped schema surface and tearing it down.

**Why this is Low and not a blocker: the placement decision is correct, on grounds the plan did not
use.** Two independent ones survive intact:

- **Ground 3 survives whole and is sufficient.** Every live probe schema reuses *fakeshop's already
  registered* types; none invents one. This row needs a throwaway `DjangoType` carrying
  `async def get_queryset`, created per test and cleared by the module's autouse registry fixture
  (`tests/test_connection.py:64-76`). A process-global fakeshop type cannot be that.
- **Rule 10's obligation is not engaged at all**, because the row earns **no new package coverage
  line** — `utils/querysets.py::reject_async_in_sync_context`'s raise is already covered by the sync
  sibling. Rule 10 and `examples/fakeshop/test_query/README.md`'s coverage rule both attach to a
  *coverage line* "earned by a real-world GraphQL query against the fakeshop schema". What this row
  pins is a **construction-time dispatch contract**, which the same README routes explicitly to the
  package tier ("package-internal coverage such as ... definition-order internals"), and which the
  target module's own docstring already cites as its reason for existing.

**Recommended change** (Worker 1's, not Worker 2's — `### Decision 1` is plan text Worker 3 may not
edit; escalated below): replace ground 2 with the tier README's own wording rather than a new
argument, and narrow ground 1 to fakeshop's **shipped** types. No test change is owed.

**Test expectation:** unchanged. No assertion in the diff depends on either ground.

#### The `-W ignore::RuntimeWarning` justification names the wrong mechanism at the scope actually recorded

The drift is **legitimate** (graded in full under `### Failability proofs` below), but its stated
reason does not survive measurement. `### Failability proofs` argues the filtered flag is licensed
because the unawaited-coroutine warning "lands as a warnings-as-errors **teardown error** ... That is
a collection/setup error, which `BUILD.md` `### What gets recorded` says is not a valid count at
all."

At the scope **actually recorded** (`-n0 -p no:randomly`), that is not what happens. My unfiltered
re-run of entry 1 at exactly that scope, with the filter dropped and nothing else changed, measured
**4 failed, 0 collection/setup errors** — the artifact rows surface as ordinary FAILED rows, not
errors. The cited licence therefore never applies to the recorded scope; the ERROR shape Worker 2
describes belongs to the `-n auto` observation its own `### Notes for Worker 3` correctly attributes
to `-n auto`. The build report's scope paragraph merges the two run modes and cites the error-count
rule for a run whose error count was always 0.

**The correct licence is the one Worker 2 also states and proved:** the artifact row set is
**non-deterministic**, and `BUILD.md` `### What gets recorded` requires node-id **sets** precisely so
a drifting set cannot be laundered into a stable-looking count. My measurement over-confirms the
non-determinism — the two artifact rows I saw
(`test_connection_resolver_async_dispatch`, `test_connection_field_omits_args_without_sidecars`) are
**two further distinct ids**, disjoint from the two Worker 2 names for the same unfiltered `-n0`
scope and from the three it names for `-n auto`. Five distinct artifact ids across the two passes.

**Recommended change:** Worker 1 corrects the reason clause when it folds the drift into
`### Decision 4`; the recommended replacement sentence in `### Notes for Worker 1 (spec
reconciliation)` currently carries the same conflation verbatim, so adopting it as written would
move the wrong reason into the plan. The measurement, the flags, and both row counts stand.

**Test expectation:** unchanged.

### DRY findings

None. The item adds one test function, no helper, no fixture, no constant, and no module-level
import; verified against the diff rather than the build report's account of it.

- **Helper reuse verified at source.** `_make_sidecar_node_type` (`tests/test_connection.py:441`) and
  `_field_schema` (`:473`) are reused as-is; `_field_schema`'s `resolver=None` default and
  `_make_sidecar_node_type`'s `total_count=False` default are read from the current file, not assumed.
- **No new module-level import.** The `git show HEAD:tests/test_connection.py` diff (read into a
  scratch path outside the repo) has hunks only at `:1022` and `:1120` — the header is untouched. The
  row's single `from asgiref.sync import sync_to_async` is function-local, matching the six sibling
  sites.
- **The `sync_to_async` hoist was correctly rejected.** Seven local copies now, but hoisting would
  edit a header a concurrent session is writing, for a seven-site refactor outside this item's
  contract. Agreed; recorded so it is not re-raised next cycle.
- **Existence challenge — I put it to the row independently and it holds, mechanically.** The
  question is whether the row duplicates its sync sibling. Under entry 2's mutation **both** rows
  fail, so the row set alone does not answer it; the **failure modes** do, and I reproduced the
  distinguishing one directly (see `### Failability proofs`). No `execute_sync` row can exhibit
  "async execution succeeded and served the seeded row"; this row is the only thing in the suite that
  can. The two rows must never be collapsed or parametrized — pytest cannot parametrize across
  execution colours, and the colour *is* the contract.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**; `git status --porcelain` over the
same path -> **no entry**. `__all__` and the re-export list are unchanged. `SyncMisuseError` was
already exported and already imported at `tests/test_connection.py:61`, so the row adds neither an
import nor an export. Matches `### Decision 7`'s stated expectation exactly.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only tracked file in
the diff is `tests/test_connection.py`; the artifact and the gitignored scratch under
`docs/builder/temp-tests/r1c/` are the cycle's own record.

### Failability proofs

**Where the second pair of eyes landed.** Both boundaries were **independently re-run by Worker 3**;
neither was accepted on Worker 2's record alone. Entry 1 was mandatory (2 rows, inside the `<= 3`
floor). Entry 2 was discretionary (11 rows, above the floor) and was re-run anyway because it is the
sole evidence the new row is not a duplicate of its sibling. A third window re-measured entry 2's
**failure mode**, which no node-id set can carry.

Every mutation was recorded in this artifact **before** it was made (see the three blocks at the top
of this review). Scratch roots outside the repository. No `git stash` / `checkout` / `restore` /
`worktree` at any point.

**Audit of Worker 2's records — every field `BUILD.md` `### What gets recorded` requires is present
for both entries**, and each was checked rather than read: boundary by symbol-qualified path; the
exact mutation (both *remove* the boundary rather than perturb code near it — verified against
`docs/builder/temp-tests/r1c/proofs.json`'s anchor/replacement blocks, which are byte-identical to
the current source); the focused scope as run, byte-identical across the two entries so the sets are
differenceable; the pre-mutation state of that same scope (`69 passed`, exit 0 — so 0 rows were
differenced out); failing node ids **listed**, never a bare count; collection/setup errors **0**,
separately; the revert proved by byte-comparison plus a `shasum` pair. `proofs-report.md` transcribes
into the artifact without drift. No zero-row entry exists, so no **why 0** judgement is owed.

**Re-run 1 — entry 1, mandatory (`utils/querysets.py::apply_type_visibility_sync` #"result = reject_async_in_sync_context(").**
Driven from a Worker-3-authored manifest (`docs/builder/temp-tests/r1c/w3-reproof.json`), same
boundary, same mutation, byte-identical scope. Report:
`docs/builder/temp-tests/r1c/w3-reproof-report.md`. Anchor matched exactly once before the copy;
pre-mutation `69 passed`, exit 0; **2 failed, 67 passed**, exit 1; **collection/setup errors 0**.

Node-id set measured — **identical to Worker 2's, as sets and as members**:

- `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse`
- `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`

Revert proved: `filecmp.cmp(shallow=False) True; sha256 6fb44ccdcb9a462d... == 6fb44ccdcb9a462d...`.
2 rows clears `### Acceptance rule` (0 or 1 is `revision-needed`). Neither of `### Decision 4`'s two
defect branches was hit.

**This entry also proves the subclass assertion is discriminating, by measurement rather than
argument.** With the guard deleted the coroutine reaches `_normalized_visibility_result` and is
rejected as a plain `ConfigurationError`; `SyncMisuseError` is a `ConfigurationError` subclass
(`utils/querysets.py:116`, `class SyncMisuseError(ConfigurationError, RuntimeError)`), so a row
asserting the **base** would have stayed green here. Both rows fail. The `isinstance(...,
SyncMisuseError)` choice is what makes the guard failable at all.

**Re-run 2 — entry 1 at the UNFILTERED scope, to grade the `-W` drift rather than accept its
account.** Same boundary and mutation, scope `tests/test_connection.py -n0 -p no:randomly` with the
warning filter dropped and nothing else changed
(`docs/builder/temp-tests/r1c/w3-reproof-unfiltered.json`). Measured **4 failed, 65 passed**,
**collection/setup errors 0**:

- `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse`
- `tests/test_connection.py::test_connection_resolver_async_dispatch`
- `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`
- `tests/test_connection.py::test_connection_field_omits_args_without_sidecars`

**Verdict on the scope drift: legitimate measurement-artifact removal, not a weakened proof.** Four
independent reasons, each checked rather than reasoned from the build report:

1. **The filtered set is a strict subset of the unfiltered set, and it is the genuine one.** The two
   surviving rows are exactly the two that assert on the guard. The two removed rows
   (`test_connection_resolver_async_dispatch`, `test_connection_field_omits_args_without_sidecars`)
   have nothing to do with `apply_type_visibility_sync` — the second is about field *arguments* — and
   are **not the two Worker 2 recorded for the same unfiltered scope**. Five distinct artifact ids
   across the two passes is the non-determinism, measured twice by different agents.
2. **The direction is conservative and cannot be gamed.** Suppressing a warning can convert
   error/fail -> pass, never pass -> fail, so a filtered count is a **lower bound**. The acceptance
   rule is a floor (`> 1`), so undercounting can only make acceptance harder. Both entries clear it
   filtered (2 and 11); unfiltered they clear it by more (4 and >= 11).
3. **The warning is manufactured by the mutation, not by the code under test.** Deleting the guard
   strands the `async def get_queryset` coroutine; the shipped tree raises no such warning
   (unmutated baseline: `69 passed`, exit 0, three separate times).
4. **The repo's `-W error` posture is untouched.** `pytest.ini`'s `filterwarnings = error` and its
   "never blanket-ignore" note govern the **ini file**, and `git status --porcelain -- pytest.ini
   pyproject.toml tests/conftest.py` is **empty** — no config was edited, in this pass or Worker 2's.
   The flag is a transient argument on a proof run over a deliberately broken tree, which is a
   different thing from weakening the suite's standing posture to make a real warning go away — the
   practice `AGENTS.md`'s async-sqlite discipline exists to forbid. **It must not be generalized**
   into a standing invocation, and the Low above asks Worker 1 to keep that distinction legible in
   the plan text.

**Re-run 3 — entry 2 (`connection.py::_build_connection_resolver` #"if resolver is None:"), discretionary.**
`docs/builder/temp-tests/r1c/w3-reproof2.json`, same mutation (`def _resolve` -> `async def
_resolve`, `return _pipeline_sync(...)` -> `return await _pipeline_async(...)`, that branch alone),
byte-identical scope. Report: `docs/builder/temp-tests/r1c/w3-reproof2-report.md`. Pre-mutation `69
passed`, exit 0; **11 failed, 58 passed**; **collection/setup errors 0**. The node-id set reproduced
**exactly — all 11 ids, same members** as Worker 2's record, the new row among them. Revert proved:
`filecmp.cmp(shallow=False) True; sha256 8db2ac5eb1bca4e5... == 8db2ac5eb1bca4e5...`.

**Re-run 4 — the failure mode, which is the item's single load-bearing claim.** `scripts/prove_failability.py`
fixes `--tb=no`, so this window used `BUILD.md`'s fenced fallback loop in its stated order (anchor
check `-> 1`; unmutated single-node run `-> 1 passed`; `cp` to a scratch path outside the repo;
mutate; run; `cp` back; `cmp`). Scope: the single new node id with `--tb=long`. Captured verbatim:

```tests/test_connection.py:1153
>       assert result.errors is not None
E       AssertionError: assert None is not None
E        +  where None = ExecutionResult(data={'items': {'edges': [{'node': {'id': 'cHJvZHVjdHMuY2F0ZWdvcnk6MQ=='}}, ...]}}, errors=None, extensions={}).errors
```

**The query succeeded and served the seeded rows** — exactly the mode Worker 2 recorded, reproduced
independently. This is what makes the row non-redundant: the sync sibling also fails under this
mutation, but on `execute_sync` meeting an awaitable, and no `execute_sync` row can ever exhibit
"async execution took a different pipeline and served the data". `cmp` exit 0; `shasum`
`e410c8682a7707c646b8b49984a1b170f7a5699a`, **identical to Worker 2's recorded before-and-after
reading** for the same file.

**No mutation is live in the tree, checked positively rather than inferred** (`BUILD.md`
`### Mutations are transient`). At the end of this pass:

| Target | `shasum` now | Worker 2's recorded before/after |
|---|---|---|
| `django_strawberry_framework/utils/querysets.py` | `4cd72adc39efafe734d2cef8db288c663b4b5cdb` | `4cd72adc...` / `4cd72adc...` |
| `django_strawberry_framework/connection.py` | `e410c8682a7707c646b8b49984a1b170f7a5699a` | `e410c868...` / `e410c868...` |
| `tests/test_connection.py` | `8a66cf2978b5a2fde41b5fd4cbbb31adc78cff3b` | `8a66cf29...` (post-ruff) |

All three match, so the tree Worker 2 handed over and the tree after four Worker 3 mutation windows
are byte-identical, and no concurrent session's bytes were clobbered by any restore. Additionally:
both anchors match exactly once; `connection.py`'s `if resolver is None:` branch still opens a plain
`def _resolve` calling `_pipeline_sync` (the only `async def _resolve` at module level is the
legitimate `elif is_async_callable(resolver):` branch); `utils/querysets.py` still carries the full
`result = reject_async_in_sync_context(...)` call; no `ACTIVE-MUTATION.json` marker exists under any
scratch root; and `uv run pytest tests/test_connection.py --no-cov` -> **69 passed**.

### Hot-path budget

**Audited, not waived.** The plan declares no hot path (`### Decision 6`) and the build report says
so. I confirmed the declaration is correct rather than accepting it: the item's net change to
`django_strawberry_framework/` is **nil** — all three targets are byte-identical to their
pre-mutation state (table above), and `git diff -- django_strawberry_framework/__init__.py` is empty.
The added code is one `async def` test function that executes only under `pytest` — not per request,
per resolver, per row, per connection, or per outbound message. No lock, no serialization point, no
added per-item work inside a queryset loop. **No before/after number is owed**, so the missing-number
Medium does not apply.

Note for the reader: on this tree "the item changed no production code" can never be proved by a
whole-package `git diff` (four concurrent cycles are writing it). The correct proof is the per-file
byte identity above, which is what both Worker 2 and this pass used.

### Floor verification

**Reproduced independently, not accepted on the record.** `BUILD.md` `## Floor verification` is the
canonical statement and was read there rather than from any restatement: **Django 5.2.16 on Python
3.10 with strawberry-graphql 0.316.0** (`docs/builder/BUILD.md:507`).

- **Venv, outside the repo**, still on disk at the recorded scratch path; `uv pip list --python
  <venv>/bin/python` re-read this pass: `django 5.2.16`, `strawberry-graphql 0.316.0`,
  `asgiref 3.12.1`; `<venv>/bin/python -V` -> `Python 3.10.19`. **All three match the canonical
  section exactly.**
- **Focused scope re-run by me**, the two node ids of `### Decision 5` and nothing wider:
  `<venv>/bin/python -m pytest "...::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse" "...::test_sync_context_async_get_queryset_raises_sync_misuse" --no-cov -p no:randomly`
  -> **`2 passed in 3.67s`**. Collection succeeded, so `### Decision 5`'s attribution caveat was never
  triggered.
- **The shared `.venv` was not mutated**, verified by reading it rather than by trusting the claim:
  `uv pip list` reports `django 6.1` / `strawberry-graphql 0.323.2`, and `.venv/bin/python -V` ->
  `Python 3.14.2`. Nothing resembling the floor landed in it, in either direction.

### Dispatched findings checklist — walk of all 14 boxes

Every box is `- [x]` and **every tick has a matching implementation**; no box is silently
unaddressed, so neither Medium in `BUILD.md` `### Dispatched findings checklist` applies. What was
checked per box, condensed:

1. Row present at the named node id, immediately after the sync sibling and before
   `test_connection_sync_resolver_returning_coroutine_raises_sync_misuse` — confirmed against the
   HEAD diff, and the placement survived the concurrent session inserting three rows *above* the
   sibling.
2. Default path — `_field_schema(node_type)` carries **no** `resolver=`; the helper's `resolver=None`
   default (`:475`) flows into `DjangoConnectionField(node_type, resolver=None)` and takes
   `connection.py:1947`'s branch. Query is the minimal `{ items { edges { node { id } } } }` — no
   `filter:`, `orderBy:`, `totalCount`, `first`/`last` — so `BUILD.md`'s right-path rule is met and no
   sidecar can silently reroute it. `_make_sidecar_node_type` is called with its defaults
   (`total_count=False`), so no generated `totalCount` subclass exists to take a different path.
3. The three assertions, in order, on the **subclass**; no `pytest.raises`, no message-substring
   assertion, no base-class assertion. Entry 1 proves the subclass choice is what makes the row
   failable.
4. Seeds first (`await sync_to_async(services.seed_data)(1)`, first statement after the local import)
   and carries `@pytest.mark.django_db(transaction=True)`.
5. No module-level import (HEAD diff hunks are at `:1022` and `:1120` only); builder wrapped via
   `await sync_to_async(_field_schema)(node_type)`.
6. / 7. Both failability entries carry every required field — audited above.
8. Both mutations reverted and byte-proved; no live mutation, verified positively above.
9. Floor verification run and recorded by this pass; reproduced above.
10. `### Hot-path budget` states `Not applicable; plan declares no hot path.`
11. `git diff -- django_strawberry_framework/__init__.py` empty; net package change nil by byte identity.
12. Ruff and `check_trailing_commas` scoped to the one file, read-only first, drift reported not applied.
13. Focused run recorded; **no `--cov*` flag appears in any command of this pass or mine.**
14. Nothing under `docs/builder/temp-tests/` deleted (`temp-tests/r1/test_async_execution_default_connection.py`
    verified still on disk); no concurrent file edited, reverted, or checked out; nothing committed;
    no branch created.

**Fixture-shape rule, re-derived independently rather than read from `### Decision 3`.** An AST walk
of the **current** module (which now has **10** async rows, not the plan's 9 — the concurrent session
added sync rows only) reproduces the rule exactly: 7/7 DB-touching async rows carry
`django_db(transaction=True)` **and** wrap their builder in `sync_to_async`; 2/2 direct-call rows
(`:1158`, `:1181`) carry neither; `:780` builds no schema and is outside both. The new row is in the
DB-touching class and follows it. The temp body's mixed shape — the one mixed shape in either class —
was correctly normalized.

### What looks solid

- **The assertion set pins the load-bearing property, not observability.** The two independent
  measurements that matter both hold: remove the guard and the row fails (entry 1); give the default
  field an async pipeline and the row fails *because the query succeeded* (re-run 4). A row that
  asserted only "an error appeared", or asserted the `ConfigurationError` base, would have survived
  entry 1 — the subclass choice is load-bearing and was made deliberately.
- **The proof discipline is the best I have audited this cycle.** Anchor-before-copy, one boundary
  live at a time, out-of-repo scratch, node ids listed rather than counted, error count carried
  separately, `shasum` pairs bracketing each window against the concurrent-writer hazard, and a
  verbatim failure-mode capture for the one claim a row set cannot carry. Every number reproduced.
- **The concurrent-writer handling is correct in both directions**: nothing reverted, nothing
  checked out, `git show HEAD:<path>` into an out-of-repo scratch used for attribution, and the two
  things that could not be fixed without writing into someone else's work were **reported** rather
  than tidied.
- **The docstring's recourse claim is true**, checked separately from the rule it supports:
  `elif is_async_callable(resolver):` (`connection.py:1976`) does emit `async def _resolve` ->
  `await _pipeline_async` -> `apply_type_visibility_async`, which awaits the hook
  (`utils/querysets.py` #"result = await result"). It also matches the module's own wording at
  `connection.py:1909`. Symbol paths only, no line numbers, ASCII, 90 characters at the longest line.
- **Both stop-and-reports were the right call**, verified rather than accepted:
  `check_trailing_commas.py --check` reproduces the failure at `tests/test_connection.py:1062`, which
  is `async def __call__(self, prefix, root, info):` inside `_Resolver` in the concurrent session's
  `test_connection_partial_async_generator_resolver_raises_sync_misuse`; `git show
  HEAD:tests/test_connection.py` contains that line **0** times. The script auto-fixes by default, so
  running it would have written into their work. And `docs/spec-030-connection_field-0_0_9.md` does
  not exist while `docs/SPECS/spec-030-connection_field-0_0_9.md` does — the module docstring's path
  is genuinely stale, genuinely pre-existing at HEAD, and genuinely outside this item's writable set.

### Temp test verification

- **Static helper skipped, with the reason recorded** (`BUILD.md` `### When to run the helper during
  build`): the diff adds no new `.py` file, touches nothing under `optimizer/` or `types/`, and adds
  31 lines to a file outside `django_strawberry_framework/` against a 50-line threshold. Worker 1's
  planning run already emitted `docs/shadow/tests__test_connection.overview.md`, and this diff adds
  no logic that would change its output. No shadow-file line number is cited anywhere in this review.
- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` — **superseded** by the
  permanent row, **retained** per the cycle's do-not-delete instruction, clears with the cycle's
  scratch. Verified still on disk, untouched.
- Worker 2's `docs/builder/temp-tests/r1c/proofs.json` and `proofs-report.md` — read as evidence,
  not edited.
- Worker 3 additions, all gitignored under `docs/builder/temp-tests/r1c/` (`.gitignore:192`):
  `w3-reproof.json` + `w3-reproof-report.md` (mandatory entry-1 re-run), `w3-reproof-unfiltered.json`
  + `w3-reproof-unfiltered-report.md` (the `-W` drift grading), `w3-reproof2.json` +
  `w3-reproof2-report.md` (entry-2 re-run). **Disposition: kept as this review's evidence; they clear
  with the cycle's scratch.** No temp test caught a behaviour bug, so nothing is owed promotion to the
  permanent suite.

### Notes for Worker 1 (spec reconciliation)

- **`Escalated:` `### Decision 1` ground 2 is false and ground 1 is overstated** (Low above). Worker 3
  may not edit plan text and Worker 2 cannot resolve it, so it comes to you. **The placement outcome
  is correct — do not re-loop the item for it.** Resolution paths: (a) replace ground 2 with
  `examples/fakeshop/test_query/README.md`'s own routing clause and narrow ground 1 to fakeshop's
  *shipped* types — the cheapest fix, and it substitutes existing wording rather than authoring a new
  claim; (b) drop grounds 1 and 2 and rest the decision on ground 3, which survives whole and is
  sufficient; (c) record it as a known imprecision in a closing artifact. My recommendation is (a),
  and the load-bearing sentence to add is that the row earns **no new package coverage line**, so
  rule 10's coverage obligation is not engaged in the first place.
- **The `-W ignore::RuntimeWarning` drift: endorsed, with its reason clause corrected.** I ran the
  unfiltered control and the flag is a conservative artifact removal (evidence under `### Failability
  proofs`). But the replacement sentence your `### Notes for Worker 1` proposes for `### Decision 4`
  repeats the "warnings-as-errors teardown error ... that is a collection/setup error" clause
  verbatim, and at the recorded `-n0` scope the artifact rows are **failures with 0 collection/setup
  errors**. Adopting it as written moves a false mechanism into the plan. Suggested substitution for
  that clause: *"the resulting unawaited-coroutine warning fails a different neighbouring row each
  run, so the unfiltered row set is non-deterministic and only the filtered set is a stable node-id
  set to difference."* Also worth a clause stating the flag is **proof-local and never a standing
  invocation** — `pytest.ini`'s `filterwarnings = error` is deliberate and was not touched.
- **Two Worker 2 stop-and-reports confirmed; one of them will meet the maintainer at commit.**
  `scripts/check_trailing_commas.py` runs in pre-commit, and it fails on `tests/test_connection.py:1062`
  — a concurrent session's line, absent at HEAD. Committing this file therefore trips the hook on
  work that is not R1c's. Name it for the maintainer in the closing artifact so it is not diagnosed
  as this item's defect.
- **The stale `docs/spec-030-connection_field-0_0_9.md` module-docstring path is confirmed real** (the
  file exists only under `docs/SPECS/`), pre-existing at HEAD, and correctly left alone. R4's
  cross-reference audit is the right home; R4 should be told the reference is in a **module
  docstring**, since a docstring edit in `tests/test_connection.py` collides with the concurrent
  session.
- **Entry 2 confirms `spec-009:417` rather than falsifying it — I reproduced the proof**, including
  the verbatim failure mode. No spec finding; R1's `final-accepted` region does not re-open.
- **Nothing else is owed.** No spec edit, no re-loop, no deferred work beyond the four items above.

### Review outcome

`review-accepted`.


No High and no Medium findings. Two Low findings, both in **plan prose rather than in the diff**,
both escalated to Worker 1 above with resolution paths, and neither resolvable by Worker 2 — the
shipped row, its assertions, its fixture shape, both failability proofs, the floor run, and the
public surface all hold as recorded, and every number in the build report reproduced independently.
All 14 checklist boxes are ticked with matching implementations. No boundary is weakly pinned; no
mutation is live in the tree.

---

## Final verification (Worker 1)

Final-verification pass run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **HEAD re-derived at the start of the pass:
`6f8bf818e9b1bc45059017c17fc346a3daca0b8f`** — unchanged from the planning and build passes, though
three commits have landed on it since the cycle's own baseline (`6f8bf818` / `58bff76a` / `7ef9f030`,
all the spec-013 residual cycle's). Nothing was accepted on Worker 2's or Worker 3's record: every
number below was re-derived at my own desk.

### The diff, read whole

`diff -u` of `git show HEAD:tests/test_connection.py` (into a scratch path **outside** the repo)
against the working tree. `git diff --numstat -- tests/test_connection.py` -> **`113 0`**: 113 added
lines, **0 deleted**, so the file is purely additive and no existing row was edited by anyone. Two
hunks: the concurrent session's **+82** (three sync rows landing *above* the sibling, including the
`_Resolver` class discussed below) and R1c's **+31** at `:1127-1156`. The R1c hunk is one
`async def` function and nothing else — no import, no helper, no fixture, no constant, no edit to the
sync sibling, no production line.

Read cold, at the symbol, in file order: the row carries `@pytest.mark.django_db(transaction=True)`;
a docstring whose every mechanism reference is symbol-qualified
(`connection.py::_build_connection_resolver`, `utils/querysets.py::apply_type_visibility_sync`,
`utils/querysets.py::reject_async_in_sync_context`) with no `path:NN` and no build-process
vocabulary; the function-local `from asgiref.sync import sync_to_async`;
`await sync_to_async(services.seed_data)(1)` as its first statement; the no-op `async def
get_queryset`; `_make_sidecar_node_type("AsyncVisibilityAsyncExecNode", get_queryset=get_queryset,)`
exploded with a trailing comma; `await sync_to_async(_field_schema)(node_type)` with **no**
`resolver=`; the minimal `{ items { edges { node { id } } } }`; and the three assertions in Decision
2's order. Measured rather than eyeballed: **max line length 90** over `:1127-1156` (limit 100), and
**0** non-ASCII characters in the whole file.

**No fail-open shape landed** (`BUILD.md` `### Fail-open shapes`). The diff adds no production line,
so the catalogued shapes have no site here; and the row's own assertion set is closed rather than
permissive — `any(isinstance(err.original_error, SyncMisuseError) ...)` is False on an empty
`errors` list, so the `errors is not None` / `any(...)` / `data is None` triple cannot pass on a
successful query. Entry 2 proves exactly that by measurement.

### Every planned step landed or was intentionally rejected

All eleven `### Implementation steps` landed as written. Nothing was rejected; nothing was deferred.
The three plan-level judgement calls all held under measurement: the placement (Decision 1, on the
corrected grounds of amendment 1), the assertion shape (Decision 2, vindicated by entry 1 — a
base-class `ConfigurationError` assertion would have stayed green under the guard mutation), and the
fixture rule (Decision 3's six-of-six DB-touching rule, which Worker 3 re-derived independently at
7/7 on the now-larger module). The two `### Implementation discretion items` Worker 2 exercised —
the `Meta.name` and the trailing comment on `assert result.data is None` — are both inside what the
plan delegated.

### Dispatched findings checklist — all 14 boxes audited against the diff

Verified rather than accepted; every tick has a matching implementation, so no box is un-ticked and
none is over-ticked. What I checked per box:

1. **Row present** at `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`,
   at `:1128`, immediately after `test_sync_context_async_get_queryset_raises_sync_misuse` and
   before `test_connection_sync_resolver_returning_coroutine_raises_sync_misuse` — read in the diff,
   and the placement survived the concurrent session's three insertions above the sibling.
2. **Default path.** `_field_schema(node_type)` carries no `resolver=`; the query is the minimal
   shape with no `filter:` / `orderBy:` / `totalCount` / `first` / `last`;
   `_make_sidecar_node_type` is called with its defaults. `connection.py:1947`'s `if resolver is
   None:` branch is the one it takes, read at source this pass.
3. **The three assertions**, in order, on the **subclass**; no `pytest.raises`, no
   message-substring-only assertion, no base-class assertion.
4. **Seeds first** and carries `django_db(transaction=True)`.
5. **No module-level import** — the HEAD diff's hunks are at `:1022` and `:1120` only; the header is
   untouched. Builder wrapped via `await sync_to_async(_field_schema)(node_type)`.
6. / 7. **Both failability entries** carry every field — audited below.
8. **Both mutations reverted**, byte-proved; no live mutation — verified positively below.
9. **Floor verification** run and recorded by the build pass; I re-ran it myself below.
10. `### Hot-path budget` states `Not applicable; plan declares no hot path.` verbatim.
11. `git diff -- django_strawberry_framework/__init__.py` -> **0 lines**, and `git status
    --porcelain` over it -> no entry. Net package change nil by the byte identity in the table below.
12. **Lint scoped to the one file, read-only first.** Reproduced this pass:
    `uv run ruff format --check tests/test_connection.py` -> `1 file already formatted`;
    `uv run ruff check tests/test_connection.py` -> `All checks passed!`.
    `scripts/check_trailing_commas.py --check` fails on `:1062` only — attributed below.
13. **Focused run recorded, no `--cov*` flag anywhere.** Grepped the whole artifact: the only
    coverage-shaped token in any command is `--no-cov`; the two bare `--cov` hits are prose about
    `pytest.ini`'s `addopts`.
14. **Nothing under `docs/builder/temp-tests/` deleted** —
    `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is on disk, 1,565 bytes,
    untouched. No concurrent file edited, reverted, or checked out; nothing committed; no branch.

### Failability proofs — records exist, complete, and no mutation is live

**Both records exist and carry every field `BUILD.md` `### What gets recorded` requires**, checked
field by field against `docs/builder/temp-tests/r1c/proofs.json` and `proofs-report.md` rather than
against the artifact's prose: boundary by symbol-qualified path; the exact mutation (the manifest
carries the literal anchor and, for entry 2, the literal replacement — entry 1 **deletes** the guard
call outright and entry 2 converts the default branch to `async def` + `await _pipeline_async`, so
both *remove* the boundary rather than perturb code near it); the focused scope as run,
byte-identical across the two entries; the **pre-mutation state of that same scope** (`69 passed`,
exit 0, so zero pre-existing rows were differenced out); the failing node ids **listed** (2 and 11
— the counts are their `len()`); **collection/setup errors 0, separately**, for both; and the revert
**proved by byte-comparison** (`filecmp.cmp(shallow=False) True` plus a matching sha256), backed by
the `shasum` pair bracketing each window. Neither entry is zero-row, so no **why 0** judgement is
owed. Both clear `### Acceptance rule` (2 > 1, and 11). The artifact transcribes the emitted report
without drift — I diffed the two by eye against `proofs-report.md`'s node-id lists and they match
member for member.

**No mutation is live in the tree, checked positively rather than inferred.** At this pass:

| Target | `shasum` now | Worker 2 before / after | Worker 3 end-of-pass |
|---|---|---|---|
| `django_strawberry_framework/utils/querysets.py` | `4cd72adc39efafe734d2cef8db288c663b4b5cdb` | `4cd72adc…` / `4cd72adc…` | `4cd72adc…` |
| `django_strawberry_framework/connection.py` | `e410c8682a7707c646b8b49984a1b170f7a5699a` | `e410c868…` / `e410c868…` | `e410c868…` |
| `tests/test_connection.py` | `8a66cf2978b5a2fde41b5fd4cbbb31adc78cff3b` | `8a66cf29…` (post-ruff) | `8a66cf29…` |

All three still match, across two builder mutation windows and four reviewer ones, so no third
party's bytes were clobbered by any restore. Structurally as well as by hash: both anchors match
**exactly once**
(`grep -c 'result = reject_async_in_sync_context(' …/utils/querysets.py` -> 1;
`grep -c 'if resolver is None:' …/connection.py` -> 1); `utils/querysets.py` still carries the full
six-line guard call; and `connection.py`'s `if resolver is None:` branch still opens a plain `def
_resolve` calling `_pipeline_sync`, with the only `async def _resolve` in `_build_connection_resolver`
sitting in the legitimate `elif is_async_callable(resolver):` branch — read at source, not grepped
for absence. No `ACTIVE-MUTATION.json` marker under the scratch root.

### Floor run — confirmed as declared, and re-run

`BUILD.md` `## Floor verification` read there as the single canonical statement: Django **5.2.16**,
Python **3.10**, strawberry-graphql **0.316.0**.

- **Isolated venv outside the repo**, still on disk at the recorded scratch path
  (`…/scratchpad/dsf-floor`), which is not inside the working tree.
- **Resolved versions re-read by me** (`uv pip list --python <venv>/bin/python`): `django 5.2.16`,
  `strawberry-graphql 0.316.0`, `asgiref 3.12.1`, `channels 4.3.2`, `django-filter 26.1`,
  `pytest 9.1.1`; `<venv>/bin/python -V` -> `Python 3.10.19`. **All three floor versions match
  exactly.**
- **Re-run by me**, the two node ids of `### Decision 5` and nothing wider, with `--no-cov`:
  **`2 passed in 3.52s`**. Collection succeeded, so `### Decision 5`'s attribution caveat never
  triggered.
- **The shared `.venv` is unmutated**, read rather than trusted: `uv pip list` -> `django 6.1`,
  `strawberry-graphql 0.323.2`, `asgiref 3.11.1`; `.venv/bin/python -V` -> `Python 3.14.2`. Nothing
  resembling the floor landed in it.

### Focused tests, run by me

`uv run pytest tests/test_connection.py --no-cov` -> **`69 passed`**. Recorded as pass/fail only, per
`## Final verification job` step 5. No `--cov*` flag was used in any command of this pass.

### DRY across this item and the prior accepted items

No new duplication. The item adds one test function, no helper, no fixture, no constant, no
module-level import, and no production line; there is nothing for a later item to duplicate and
nothing here that duplicates R1 or R1b (both documentation-only). The `sync_to_async` hoist stays
correctly rejected — seven function-local copies now, and hoisting would edit a header a concurrent
session is writing for a seven-site refactor outside this item's contract. The condition that would
justify it is already recorded in `### DRY analysis` and is not met.

### The two Low findings, resolved

Both were plan prose, both mine to fix, and both are corrected **in place with a marked
final-verification amendment** rather than silently rewritten — the builder built against the
original text, so the record has to show what moved.

- **Low 2 (`### Decision 1`) — amendment 1.** Ground 2 was false and I re-derived the disproof
  myself rather than reading Worker 3's: `_probe_async_view` mounts `AsyncDjangoGraphQLView` on a
  real event loop in `test_error_policy_api.py` (`:192`) and `test_resource_policy_api.py` (`:124`),
  and `test_transport_api.py` mounts the same view at `:239`, `:381`, `:398`. Ground 2 is
  **withdrawn**, ground 1 narrowed to fakeshop's *shipped* types, and Worker 3's decisive ground
  added as ground 0: the row earns no new package coverage line, so rule 10's coverage obligation is
  not engaged at all, and `examples/fakeshop/test_query/README.md` routes package-internal coverage
  to the package tier. That ground is measured, not argued — entry 1's node-id set is exactly the
  new row and its sync sibling, which is what "same package boundary, already covered" looks like
  when you measure it. **Placement outcome unchanged; no re-loop, no test change.**
- **Low 1 (`### Decision 4`) — amendment 2.** The scope drift is folded in with the **correct**
  licence. Worker 2's stated reason (a collection/setup error, which `BUILD.md` grades as no valid
  count) does not survive at the recorded `-n0` scope, where Worker 3's unfiltered control measured
  4 failed / **0** collection-setup errors; that ERROR shape belongs to `-n auto`. The licence is
  **non-determinism**: the two passes' unfiltered artifact-row pairs are disjoint (Worker 2's two ids
  vs Worker 3's two further ids), and `### What gets recorded` requires a node-id **set**, which a
  drifting set cannot be. Worker 2's proposed replacement sentence repeated the false clause
  verbatim, so it was **not** adopted; the amendment writes the correct mechanism instead, and adds
  the clause that the flag is proof-local and never a standing invocation — `pytest.ini`'s
  `filterwarnings = error` is untouched (`git status --porcelain -- pytest.ini pyproject.toml
  tests/conftest.py` -> empty), and `AGENTS.md`'s standing rule that async-sqlite ResourceWarnings
  are never fixed by weakening `-W error` must not be read as loosened by a transient argument on a
  proof run over a deliberately broken tree.

### Two things for the maintainer, report-only

- **`scripts/check_trailing_commas.py` runs in pre-commit and WILL fail on
  `tests/test_connection.py:1062` at commit time.** Reproduced this pass:
  `tests/test_connection.py:1062: should explode (>= threshold, no trailing comma)`, exit 1. That
  line is `async def __call__(self, prefix, root, info):` inside `_Resolver` in a **concurrent
  session's** uncommitted row — `grep -c` of that exact line against
  `git show HEAD:tests/test_connection.py` (read into an out-of-repo scratch path) returns **0**, and
  it sits at `:1062`, outside R1c's `:1127-1156`. Worker 2 correctly refused to run the script's
  auto-fix over another session's work. **This is the one thing that will bite at the commit gate,
  and it is not R1c's**; the fix belongs to whoever commits that row.
- **The module docstring's stale spec path.** `tests/test_connection.py:3` reads
  ``Spec: ``docs/spec-030-connection_field-0_0_9.md``` while the file exists only at
  `docs/SPECS/spec-030-connection_field-0_0_9.md` (both checked on disk this pass). Pre-existing at
  HEAD, outside this item's writable set, and R4's cross-reference audit is the right home. R4 should
  be told it is in a **module docstring**, since that edit collides with the concurrent session.

### Staged anchors

`grep -rn 'TODO(spec-009\|TODO-<MILESTONE>-009'` over `tests/test_connection.py` -> none. This item
is not a doc-wrap or final in-spec slice, so the tree-wide sweep stays R4's, per the build plan.

### Summary

R1c shipped one permanent test row, `tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse`
(+31 lines, 0 deletions, no production change), pinning that a **default** `DjangoConnectionField`
over a type declaring `async def get_queryset` surfaces `SyncMisuseError` as a top-level GraphQL
error with `data is None` under `await schema.execute` — the async twin of a sync-only contract, and
an executable proof that `connection.py::_build_connection_resolver` fixes the sync/async pipeline
choice at **construction** rather than per execution. Two failability proofs (2 rows and 11 rows,
0 collection errors, both reverts byte-proved and independently reproduced) and a floor run at
Django 5.2.16 / Python 3.10.19 / strawberry-graphql 0.316.0 back it. The cycle's only code-writing
item closes with the guard it names failable, the row non-redundant against its sync sibling by
measured failure mode, and no production line touched.

### Spec changes made (Worker 1 only)

**None.** No spec or rationale text was edited by this item, and none is owed: entry 2's measurement
**confirms** `spec-009:417`'s corrected wording (default field, sync pipeline, choice fixed at
construction) rather than falsifying it, so R1's `final-accepted` region does not re-open — the
discriminator is falsity, not resemblance, and there is no falsity here. Every
`### Dispatched findings checklist` box is `- [x]` with a landed contract, so no deferral reason is
owed for any box. The spec's status/header lines were re-verified at the start of this pass and
still describe the build's current state.

Two amendments were made to **this artifact's own `## Plan (Worker 1)` section** — not to the spec —
resolving the review's two Low findings, each marked inline as a final-verification amendment:
`### Decision 1` (grounds corrected: ground 2 withdrawn, ground 1 narrowed, ground 0 added) and
`### Decision 4` (focused scope folded in at the scope as run, with the non-determinism licence
replacing the false collection/setup-error one).

### Final status

`final-accepted`.
