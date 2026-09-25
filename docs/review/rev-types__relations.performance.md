# Review · Performance: `django_strawberry_framework/types/relations.py`

Status: verified
Run: 0.0.15 2026-09-25-2

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=b43e2f2fb07e4c13ee93056c09a5a94ede07065f

## Trace

Target read whole (109 lines, blob `4098eebc`); `git diff <ITEM_BASELINE> -- django_strawberry_framework tests`
is empty, so the tree reviewed is the item baseline. Orientation:
`review_inspect.py` overview at `<root>/performance/inspect/` (json `<root>/performance/relations.json`):
0 per-row leads, 0 hot entry points, 0 import-time work, 0 ORM markers, one call of interest
(`tuple()` in `PendingRelation.__hash__`).

Symbols and every production caller (`rg` over `django_strawberry_framework/`, tests and examples):

- `django_strawberry_framework/types/relations.py::PendingRelation` constructed only in
  `django_strawberry_framework/types/base.py::_build_annotations`, once per auto-synthesized
  relation field, reached from `DjangoType.__init_subclass__` (class declaration) and appended via
  `django_strawberry_framework/registry.py::TypeRegistry.add_pending_relation`. Read only by
  `django_strawberry_framework/types/finalizer.py::finalize_django_types` (Phase 1 loop, field
  reads + one `definition.field_map` lookup per record),
  `django_strawberry_framework/types/finalizer.py::_format_unresolved_targets_error` (error path),
  `django_strawberry_framework/registry.py::TypeRegistry.discard_pending` (id-set filter) and
  `django_strawberry_framework/registry.py::TypeRegistry.unregister` (list filter by
  `source_type is`). No optimizer, resolver, connection or request-time module imports the
  module or its symbols.
- `django_strawberry_framework/types/relations.py::PendingRelation.__hash__` and
  `django_strawberry_framework/types/relations.py::_hash_component`: no production caller.
  `discard_pending` matches by `id()`; no set, dict key or `in` test over records exists in the
  package. Only `tests/types/test_relations.py` hashes records.
- `django_strawberry_framework/types/relations.py::PendingRelationAnnotation` /
  `_PendingRelationAnnotationMeta.__repr__`: installed as an annotation value at declaration,
  rewritten by `finalize_django_types`; the repr runs only in Strawberry's schema-construction
  `TypeError` when finalize was skipped.

`Path class: cold` - every executable line runs at class declaration (`__init_subclass__`) or
once per `finalize_django_types()` call (schema build); nothing runs per request, resolver, row,
connection or outbound message.

Measurements, copy `review/types/relations.py/performance`, package digest
`sha256:ffacb690...b08dcb` (the tree as it stands after the utils/strings.py item; it is not the
`## Bench baseline` digest `df761b82...`, so these figures are self-referenced, and no bench
figure is claimed to move):

- `review-20260925T170201-ddae3e`: `python <root>/performance/probe_pending.py
  <root>/performance/probe_pending.json` (probe blob `48640cf7`, `_bench_common.py` `253a3953`,
  in-memory SQLite). Importing `config.schema` (every fakeshop app declared and finalized)
  calls `add_pending_relation` 178 times, `discard_pending` receives 178 records,
  `PendingRelation.__hash__` is called 0 times. timeit median of 9 x 100k, loop baseline 8.8 ns:
  construct with a forward FK 583.8 ns, with a reverse rel 541.0 ns; `hash()` 586.1 / 958.2 ns.
  Construction total per schema build = 178 x 584 ns ~= 104 us, once per process. The copy
  synced from the shared tree as it stood, which carries concurrent `examples/fakeshop/apps/library/`
  edits (a new library model), so 178 is a fixture-dependent volume, not a pinned count; no
  conclusion rests on its exact value.
- `review-20260925T170214-fc9978`: `python scripts/importtime_report.py --rounds 5 --top 80 --json
  <root>/performance/importtime.json` (instrument blob `15f679c9`, which differs from the bench
  baseline's `bfce84b9`, so it compares to nothing there): `django_strawberry_framework.types.relations`
  self 0.3 ms, cumulative 0.3 ms, of package cumulative 177.7 ms over 67 modules. Its imports
  (`dataclasses`, `django.db.models`, `..utils.relations`) are already pulled in by the package
  import through `types/base.py` and `registry.py`. `audit` reports `shared=moved 1` for this
  run (concurrent work landed after the sync); the package digest equals the probe run's, so
  both runs measured the same package bytes.

Cells: default, sharded, pg all `inapplicable by construction`: the module opens no connection,
reads no alias, runs no query and makes no dialect decision; `django.db.models` is imported for
annotations only (`from __future__ import annotations`), and its inputs are Django field objects
and classes at declaration time. No `count_queries.py` run: nothing here reaches the database.

Fingerprints (`git hash-object`): `django_strawberry_framework/types/relations.py`
4098eebca9b9fad9e328bdbc920ff863e3a229e9; `django_strawberry_framework/registry.py`
9cc8bb553fd417fc465809a541769a8383469cda; `django_strawberry_framework/types/base.py`
49057fad2058ee63635c7951bfcd7ab8d9a0be30; `django_strawberry_framework/types/finalizer.py`
de34ae2aaed10fd664197cc2205c29e7d1927c2d; `django_strawberry_framework/utils/relations.py`
8dbc3fe668dda7d57f1e2b2a3af66afdda449ded; `tests/types/test_relations.py`
bff8c265cc6baa956feb0a76b5e846c09bb58a42; `scripts/importtime_report.py`
15f679c9ad736b71215d8ead0733116f56083cef; `scripts/_bench_common.py`
253a39533f35b94f6afb7a1167c2c38489bbbbef.

## Findings

### High

None.

### Medium

None.

### Low

None.

Looks-for discharge (REVIEW.md "Performance"):

- N+1 / per-row queries, `await` per row, `.filter()` on a prefetch: none; the module runs no query.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none; no queryset.
- `only()` / `defer()` deferred loads: none.
- unbatched writes: none; no writes.
- `blog.id` vs `blog_id`: none; no model instance access (`field.related_model` is read in the
  producer, a class attribute).
- repeated `_meta` walks, settings reads, regex compilation, schema or type lookups per request:
  none; no `_meta`, settings or regex in the module, and nothing runs per request.
- `lru_cache` on methods (`B019`): none.
- locks, cache reads, re-parses, extra round trips on a per-request path: none; no per-request path.
- import-time cost: 0.3 ms self, no settings read, no work at import beyond two class bodies and
  one dataclass decoration (`review-20260925T170214-fc9978`); see rejection R3.
- allocation in the walk: the walker never touches the module; the one allocation site
  (`tuple(...)` in `__hash__`) has no production caller; see rejection R1.

## Rejected

- **R1: `PendingRelation.__hash__` builds a generator and a 7-tuple per call.** 586-958 ns per
  hash (`review-20260925T170201-ddae3e`), but 0 calls in a full fakeshop declaration + finalize;
  only `tests/types/test_relations.py` hashes records. Cold and unreached: plainness wins.
  Reopens if a production path hashes records (a set, dict key or `in` test over
  `PendingRelation` in `registry.py` or `types/finalizer.py`) on a path that runs per request.
- **R2: frozen-dataclass construction (`object.__setattr__` per field) or `slots=True`.**
  ~584 ns per record, 178 records ~= 104 us once per schema build. Declaration-time cost; no
  stated reason to trade plainness for it. Reopens if `PendingRelation` is constructed per
  request, or a bench shows declaration + finalize dominated by record construction.
- **R3: import-time cost of the module.** 0.3 ms self of 177.7 ms package cumulative; its imports
  are already loaded by `types/base.py` and `registry.py`, so lazy-importing it would move nothing.
  Reopens if the module gains import-time work or an import no sibling already pays.
- **R4: `TypeRegistry.discard_pending` / `unregister` rebuild the pending list.** O(n) list
  rebuilds of at most 178 records, once per finalize / per unregister; cold, and in
  `registry.py`, which is not this item's target. Reopens under a `registry.py` item if finalize
  is called repeatedly per process on a hot path.

Observations passed to Mechanics (not performance findings, no reachable input here):
`_hash_component` catches `BaseException`, which would also swallow `KeyboardInterrupt` /
`SystemExit` raised inside a field's `__hash__`; and `__hash__` + `_hash_component` have no
production caller (measured 0 calls above), existing to keep records usable as set members, a
behavior only `tests/types/test_relations.py` pins. Whether either is a finding is Mechanics'
call on its contract sources.

Handoff: Cold module end to end; 178 pending records per fakeshop build, zero production hashes,
~104 us construction per process, 0.3 ms import. Probe source and JSON kept under
`docs/review/temp-tests/types__relations/performance/` for any verifier; with no findings there is
no Proof line to run. The package digest measured (`ffacb690`) is the post-utils/strings.py tree,
not the bench baseline's; the importtime instrument blob also changed since the baseline
(`bfce84b9` -> `15f679c9`), so no figure here compares to `## Bench baseline`. Other axis records
did not exist when this pass read the tree; the two Mechanics observations above are the only
open thread.

## Verification (Performance)

Pass 1, address `review/types/relations.py/verify-performance-1`.

Diff binding: `git diff b43e2f2fb07e4c13ee93056c09a5a94ede07065f --` the nine item paths hashes
`d1dad86b...67664499`, equal to `docs/review/temp-tests/types__relations/diff/pass-1.diff`.

Proof lines: none to run. This record holds no findings; neither the Mechanics nor the Comments
record has a `## Cross-axis (for Performance)` section. Worker-2 claims no number for this axis
("No bench figure moves"), so there is nothing to reproduce.

Whole-diff reading through Performance. Production hunks: `types/relations.py` (`eq=False`,
`__hash__` + `_hash_component` deleted, `relation_kind` / `nullable` fields and the `RelationKind`
import deleted, prose) and `types/base.py::_build_annotations` / `DjangoType.__init_subclass__`
(`field_map` parameter, the `field_map[field.name]` lookup per relation field and two kwargs
removed). Every line runs at class declaration or once per `finalize_django_types()`; the diff
adds no call, lookup, allocation or import on any path, and no hot path (resolver, optimizer,
connection, request) reaches either file's changed symbols. `Path class: cold` stands.
`eq=False` changes no consumer's cost shape: `TypeRegistry.discard_pending` filters by `id()`,
`TypeRegistry.unregister` by `is not`, the finalizer keeps records in lists and never tests
membership (`rg -n pending` over `registry.py` and `types/finalizer.py`).

Attacks, interleaved before / after / before / after, probe
`<root>/verify-performance-1/probe_pending_v.py` (blob `183ce322`, adapts its kwargs to the
dataclass's field set; `_bench_common.py` `253a3953` both sides; in-memory SQLite), timeit median
of 9 x 100k; before at `review/types/relations.py/before` (read-only, not `--fresh`, `copy is
fresh`, digest `ffacb690...b08dcb` = the review pass's digest), after at this address (digest
`ddeafdd5...16dfb9`):

| Run | Copy | Records added / discarded | `__hash__` / `__eq__` calls | construct fwd / rev ns | hash fwd / rev ns |
|---|---|---|---|---|---|
| `review-20260925T172402-7ef1de` | before | 176 / 176 | 0 / 0 | 848.9 / 802.5 | 568.7 / 931.0 |
| `review-20260925T172409-a8e08d` | after | 178 / 178 | 0 / 0 | 698.9 / 635.6 | 17.7 / 20.6 |
| `review-20260925T172414-b87e93` | before | 176 / 176 | 0 / 0 | 868.3 / 824.4 | 565.3 / 947.2 |
| `review-20260925T172420-f3ca05` | after | 178 / 178 | 0 / 0 | 686.4 / 637.2 | 18.6 / 17.8 |

Construction ~18-23% cheaper (two fewer frozen-field `object.__setattr__` calls), hash ~30-50x
cheaper (identity), both on a cold path; still 0 hash and 0 eq calls in a full fakeshop build, so
the hash figure moves no real cost. The 176 vs 178 record count is the concurrent library model
(the before copy synced before it), not this change; no conclusion rests on it. Import time,
`review-20260925T172440-929608` (`importtime_report.py --rounds 5 --top 80 --json
<root>/verify-performance-1/importtime.json`, instrument `15f679c9` = the review pass's):
`django_strawberry_framework.types.relations` self 0.2 ms cumulative 0.2 ms (review pass: 0.3 /
0.3), package 67 modules; dropping the `utils.relations` import moves nothing, since `registry.py`
and `types/base.py` still load it. No figure here is compared to `## Bench baseline` (digest and
importtime instrument differ from the baseline's, as the review pass recorded).

Cells: `sharded`, `pg` still `inapplicable by construction`; the diff adds no query, alias or
dialect decision.

Disputes: none on this axis. Failability: no test pins a Performance claim of this item (no
finding), so no `prove` manifest is owed on this axis.

Fingerprints (`git hash-object`): `django_strawberry_framework/types/relations.py`
5e9b5cdbc7fb919f15afef090a2aae5c7663b706; `django_strawberry_framework/types/base.py`
dda91365a7e8cb146d718b6f61b95e4821d6a555; `django_strawberry_framework/types/finalizer.py`
de34ae2aaed10fd664197cc2205c29e7d1927c2d; `django_strawberry_framework/registry.py`
9cc8bb553fd417fc465809a541769a8383469cda; probe 183ce322cd8d7e9ef8d9470642534ad6523b4f2c;
`scripts/_bench_common.py` 253a39533f35b94f6afb7a1167c2c38489bbbbef;
`scripts/importtime_report.py` 15f679c9ad736b71215d8ead0733116f56083cef.

Record checks: `workspace.py audit` on this record, 7 run ids, all `ok`, each in its own
address's copy. `check_citations.py --paths` on this record: 2 unresolved, both in the review
pass's `## Trace` (`types/relations.py::PendingRelation.__hash__`, `types/relations.py::_hash_component`),
which describe the item-baseline tree; the change deleted both symbols on purpose (Mechanics M1).
Left as written (prior pass's text, nothing lands in code or a standing doc from it).

Verdict: verified.

Handoff: nothing open on Performance. The change only makes a cold record cheaper; R1-R4 stay
rejected and R1's trigger is now moot (`__hash__` is gone, identity hash is C-level). Probe,
JSONs and importtime output under `docs/review/temp-tests/types__relations/verify-performance-1/`.
I did not grade the `field_map` parameter removal beyond cost (Mechanics' call, per Worker-2's
handoff).
