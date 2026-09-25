# Review · Performance: `django_strawberry_framework/utils/strings.py`

Status: verified
Run: 0.0.15 2026-09-24-1

## Trace

Target read whole at blob `3ec3b262`. Release change (`git diff 0.0.14..HEAD`, commit a8f31a2d):
`pascal_case` now preserves leading/trailing underscore runs (two slices + an f-string); every
other symbol unchanged this release, all reviewed as they stand.

Callers (`rg` over `django_strawberry_framework/`, 30 call sites), classified by what runs them:

- Hot (per request on a plan-cache miss, and on every request for a non-cacheable plan):
  `snake_case` from `django_strawberry_framework/optimizer/walker.py::_resolve_selection_target`,
  `django_strawberry_framework/optimizer/walker.py::_walk_selections` (unresolved fallback) and
  `django_strawberry_framework/optimizer/walker.py::_selected_scalar_names`, one call per
  selection. `flatten_lookup_path` from
  `django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions`, one call per
  to-many order entry per request, beside `classify_path` + an aggregate build that dwarf it.
- Hot but memoized upstream: `flatten_lookup_path` via
  `django_strawberry_framework/utils/permissions.py::_check_method_name` (`lru_cache(2048)`),
  so it runs once per declared path per process.
- Cold (declaration / finalize / schema build / management command): every `pascal_case`,
  `pascal_case_or_raise`, `graphql_camel_name` caller (`types/converters.py`, `mutations/inputs.py`,
  `forms/inputs.py`, `rest_framework/*`, `utils/inputs.py`, `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`,
  `filters/inputs.py::_pascal_case`), and the `snake_case` callers in `types/base.py`,
  `types/finalizer.py`, `management/commands/inspect_django_type.py`.

Measurements, all in copy `review/utils/strings.py/performance`, package digest
`sha256:df761b82...9f3130` = the `## Bench baseline` digest:

- `review-20260925T033654-ee614b`: `python probe_snake_case.py <root>/performance/probe_snake_case.json`
  (probe source `<root>/performance/probe_snake_case.py`, copied into the copy root; captures the
  four `bench_optimizer_walk.py` candidates through its own `_capture_walk_inputs`). `snake_case`
  calls per walk: glossary scalar 4, nested 11, deep 39, products connection 2. Schema-wide
  GraphQL field-name vocabulary 708 vs `lru_cache` maxsize 2048. Warm per-call ns (loop baseline
  19.9): `snake_case` 70.9, `_snake_case_cached` direct 26.0. `flatten_lookup_path("category__name")`
  119 ns.
- `review-20260925T033740-60a264`: `python probe_plain_text.py <root>/performance/probe_plain_text.json`
  (source `<root>/performance/probe_plain_text.py`), timeit median of 9 repeats, 300k calls,
  loop baseline 22.8 ns: see finding L1.
- `review-20260925T033834-757fb7`: `python scripts/importtime_report.py --rounds 5 --top 80 --json
  <root>/performance/importtime.json`: `django_strawberry_framework.utils.strings` self 83 us,
  cumulative 83 us, of package cumulative 196.5 ms.
- `review-20260925T033849-1e6564`: `snake_case.__doc__` at runtime (Cross-axis, below).

Cells: default, sharded, pg all `inapplicable by construction`: the module opens no connection,
reads no alias, makes no dialect decision and imports no ORM symbol; its inputs are Python
strings.

Fingerprints (`git hash-object`): `django_strawberry_framework/utils/strings.py` 3ec3b262ea8666d4ba36cf83807ca377fee5a680;
`optimizer/walker.py` 611e8fae4985321c24f09ab4891e23079f7e1b18; `orders/sets.py`
6044ab1a11c77a42b715f0d0722fe7c9695064bc; `utils/permissions.py` 9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec;
`utils/__init__.py` 1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee; `utils/inputs.py`
ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0; `sets_mixins.py` ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3;
`filters/inputs.py` 82b52d97b8f8b26d2846df24dabcabb793507c87; `exceptions.py`
e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b; `tests/utils/test_strings.py`
3dad1a9d42d88a061546f5ee11a37ca453436c4e; `scripts/bench_optimizer_walk.py`
de745175799b1d8c0efa5c75cd296f9dd6910e34; `scripts/importtime_report.py`
bfce84b9c167ca9720f8e4f839cae45fd3702f6c.

## Findings

### High

None.

### Medium

None.

### Low

#### L1: `_plain_text` tests the rare case before the common one

- **Observation** — `django_strawberry_framework/utils/strings.py::_plain_text` runs
  `isinstance(value, str)` before `type(value) is str`, so every exact-`str` call (every call the
  walker makes: `sel.name` comes from graphql-core's AST) pays the `isinstance` builtin call
  before the identity test that returns it. All five public helpers enter through it.
- **Evidence** — `review-20260925T033740-60a264`, warm, same names: `_plain_text` shipped 38.7 ns
  vs exact-`str`-first 30.1 ns (net of loop 15.9 vs 7.3); `snake_case` 70.6 vs 63.6 ns. Parity
  asserted in the probe on `str`, a `str` subclass, and `None` / `3` / `b"x"` (same return type,
  same `ConfigurationError`).
- **Impact** — Path class hot: the walker calls `snake_case` once per selection on every plan
  build (plan-cache miss, every non-cacheable request); 39 calls on the deep glossary shape, so
  about 0.3 us of the 154.33 us `bench_optimizer_walk.py` glossary-deep median (baseline
  `review-20260925T033406-a529d7`). Below that bench's spread: it cannot resolve the move, and no
  query count exists to pin.
- **Severity** — Low: bounded hot-path saving under 1% of the walk, invisible end to end.
- **Recommendation** — at the owner, reorder to `if type(value) is str: return value`, then the
  `isinstance` rejection, then `return str.__str__(value)`. Same three branches, no new code.
- **Must not change** — non-`str` input raises `ConfigurationError` with "must be a string"; a
  `str` subclass (including one whose `__str__`, `__hash__`, `split`, `replace` raise) is
  normalized through `str.__str__` to an exact `str` before any method or cache lookup; exact
  `str` returned unchanged.
- **Proof** — at `review/utils/strings.py/verify-performance-<n>`: copy
  `<root>/performance/probe_plain_text.py` into the copy root, run
  `workspace.py run <address> -- python probe_plain_text.py <root>/verify-performance-<n>/probe_plain_text.json`;
  landed = `parity: ok` and (`plain_text shipped` - `plain_text reordered`) <= 2.0 ns (before:
  8.6 ns); and `workspace.py run <address> -- pytest tests/utils/test_strings.py --no-cov`
  passes (`test_string_helpers_normalize_hostile_string_subclasses`,
  `test_string_helpers_reject_non_string_inputs` pin the Must-not-change rows). Bench figure:
  none moves measurably; this is the micro-benchmark claim only.
- **Freshness** — `utils/strings.py` 3ec3b262; `exceptions.py` e06b0b7f; `tests/utils/test_strings.py` 3dad1a9d.

## Rejected

- **Inline exact-`str` fast path in `snake_case`** (bypassing the `_plain_text` frame: 48.2 vs
  70.9 ns per call, `review-20260925T033654-ee614b`; walk replay interleaved 7 x 5000, deep 155.1
  vs 150.5 us, nested 85.2 vs 85.0 us, within run spread). Rejected: it respells the
  normalization guard at a second site for a sub-1% walk saving; plainness wins. Reopens if a
  measured walk shows `snake_case` above 2% of `bench_optimizer_walk.py` time (a schema whose
  non-cacheable operations select thousands of fields per request).
- **`lru_cache(maxsize=2048)` sizing** on `django_strawberry_framework/utils/strings.py::_snake_case_cached`.
  Walker inputs are validated GraphQL field names, so the key set is bounded by the schema
  vocabulary (708 in fakeshop, 2.9x headroom); cache hits after warm-up. Reopens if a supported
  schema exceeds 2048 distinct field names, where a cyclic walk order would thrash LRU; the fix
  then is sizing from the schema, not `maxsize=None`.
- **Char-by-char rebuild in `_snake_case_cached`** (list append per character): runs once per
  distinct name per process behind the cache; cold.
- **`camel +=` string building in `graphql_camel_name`; slices and join in `pascal_case`** (incl.
  this release's leading/trailing slices): cold, every caller is declaration or finalize time;
  plainness wins.
- **`while "__" in flattened: replace` in `flatten_lookup_path`**: 119 ns per call, one call per
  to-many order entry per request next to path classification and an aggregate; the permission
  mangle is memoized upstream. A regex would be slower and less plain.

Looks-for discharged, `none`: N+1 / per-row queries, `len(qs)` / `bool(qs)`, `only()` /
`defer()`, unbatched writes, `blog.id` vs `blog_id` (no ORM use); repeated `_meta` walks,
settings reads, regex compilation, schema or type lookups (none in the module); `lru_cache` on
methods / B019 (the one cache decorates a module function); locks, cache reads, re-parses, round
trips on a per-request path (only the `lru_cache` lookup, the intended memo); import-time cost
(83 us self, stdlib-only imports plus `exceptions`, no settings read at import); allocation in the
walk (cached path allocates nothing; only L1's call-order cost remains).

## Cross-axis

None placed here by other reviewers at close.

Out-of-axis lead for Comments, routed through Worker-0 because `rev-utils__strings.comments.md`
did not exist when this pass closed (creating it would race its owner):
`django_strawberry_framework/utils/strings.py::snake_case` carries a literal docstring
("Normalize ``name`` before consulting the bounded conversion cache.") that never exists at
runtime: `functools.wraps(..., assigned=(..., "__doc__", ...))` replaces it with
`_snake_case_cached.__doc__` at import (`review-20260925T033849-1e6564` prints the cached
function's first line). Dead text on a public symbol; Comments owns the grade.

Handoff: Read beyond the trace: `scripts/bench_optimizer_walk.py` capture path (reused in the
probe), `tests/utils/test_strings.py` whole. The only hot entry into this module is the walker's
per-selection `snake_case`; everything else is build time or memoized, so the module has no
query or bench-visible cost. L1 is a micro saving the bench cannot resolve; if Worker-2 lands no
other change in `strings.py` it is a deferred Low by REVIEW "Severity". The verifier should
check the reordered `_plain_text` still reaches `str.__str__` for subclasses (the hostile
subclass test covers it). The `snake_case` duplicate call in `_walk_selections`' fallback branch
(after `_resolve_selection_target` already reversed the same name) is walker-owned, miss-path
only, not this item's edit. Probes and JSON under
`docs/review/temp-tests/utils__strings/performance/`.

## Verification (Performance)

Address `review/utils/strings.py/verify-performance-1`, copy synced from the shared tree at
digest `sha256:a7408aee...c703e8` (= Worker-2's final digest), copy `fresh` at first run; scratch
`docs/review/temp-tests/utils__strings/verify-performance-1/`. Item diff
`docs/review/temp-tests/utils__strings/diff/pass-1.diff` (12 files).

Proof results (run before reading `## Implementation (Worker-2)`):

- L1 probe, `review-20260925T035708-962a32` (`probe_plain_text.py` copied to the copy root,
  JSON `verify-performance-1/probe_plain_text.json`): `plain_text shipped` 30.0 ns vs
  `reordered` 29.4 ns, delta 0.6 ns <= 2.0 bound; `parity: ok`. Landed.
- `pytest tests/utils/test_strings.py --no-cov`, `review-20260925T035715-1c1132`: 41 passed. Landed.

Numbers reproduced:

- Before, read-only at `review/utils/strings.py/before` (probe by absolute path, copy not
  edited), `review-20260925T035730-bad80a`, digest `sha256:df761b82...9f3130` (= `## Bench
  baseline`): shipped 37.5 vs reordered 28.5, delta 9.0 ns (Worker-2 8.4, reviewer 8.6);
  `snake_case` 68.0 vs 62.9. After (above) 0.6 ns, matching Worker-2's 0.6 ns
  (`review-20260925T035407-988276`).
- Worker-2's "44 passed" (`review-20260925T035345-9110fa`) = `test_strings.py` 41 +
  `test_init.py` 3; its scope line confirms. `workspace.py audit docs/review/rev-utils__strings.md`:
  every Worker-2 run id `ok`, package and database inside the copy.

Failability, `workspace.py prove review/utils/strings.py/verify-performance-1
<root>/verify-performance-1/l1.json`, `review-20260925T035811-98e2b4`, exit 0, restore
byte-checked (blob 536d175c before and after):

1. L1 reverted (isinstance rejection first) over `tests/utils/test_strings.py`: behaviour
   preserved, `expect_failing: []` met (41 passed both runs). L1 is timing-only, as recorded.
2. Positive control, `return str.__str__(value)` -> `return value`: exactly
   `test_string_helpers_normalize_hostile_string_subclasses` fails (1 row).
3. Positive control, rejection deleted: exactly the 4 `test_string_helpers_reject_non_string_inputs`
   rows fail.
   So both Must-not-change rows are pinned under the reordered code. Row 2 is one node: a
   pre-existing test's granularity, not a boundary this item adds.

Whole-diff reading (Performance): production changes are L1 (hot, measured above); M1's
`field_map` key change in `types/base.py`, `types/finalizer.py`, `inspect_django_type.py` (cold:
declaration, finalize, management command; it drops one `snake_case` call per field there, a cold
saving nobody needs to measure); `functools.wraps` `assigned` minus `__doc__` (import time, no
per-call effect); docstrings. The walker's code is unchanged; its `field_map` lookups now index
raw names, identical to snake keys for every lowercase Django name (Mechanics'
`review-20260925T033937-78b854`).

Attacks:

- Walk bench, interleaved `before` / verify copy x2, same instrument blob de745175:
  `review-20260925T035834-cc9ba2`, `-035900-77a1f3`, `-035935-3a710b`, `-040002-00b01e`. Plan
  shapes identical on all four candidates (`sr/pf/only/fk/keys` 0/0/4/0/0, 0/5/1/0/5,
  0/6/4/1/10, 0/0/2/0/0). Deep median before 195.35 / 180.83 vs after 213.25 / 169.19 us, nested
  111.21 / 97.29 vs 110.00 / 95.67: the order alternates, run-to-run swing (~15%) exceeds any
  difference on this loaded machine, and every figure sits above the 154.33 us baseline for the
  same reason. No regression is visible; none is expected, since fakeshop's maps are unchanged.
- Mixed-case query shape at a second cardinality: Worker-2's
  `test_mixed_case_relation_selections_plan_through_their_django_names` pins `{1: (1, 2), 3: (1, 2)}`
  (batched, absolute counts); both new nodes pass in my copy, `review-20260925T040024-60fb84`.
- Mixed-case selection on the walker's hot path, probe `verify-performance-1/test_zz_probe_miss.py`
  (copied to `tests/optimizer/` in the copy), `review-20260925T040111-52f3c0`, 21-field
  `managed=False` type, `info=None`: reversible lowercase hit `plainJ` 150.4 ns per
  `_resolve_selection_target` call; mixed-case `mixedCase0` 7544.5 ns, `mixedCase9` 8437.8 ns (the
  reverse lookup misses, `_graphql_names_by_python_name` rebuilds the type's name dict, then
  `_field_by_graphql_name` scans the map). A first run, `review-20260925T040057-e51263`, used
  `plain9` as the control and measured 8144.1 ns: a digit-boundary name takes the same miss path
  today. Not a finding against this item: before the change a mixed-case selection crashed the
  query (M1), so there is no working "before" to regress from, and the miss path's cost is
  pre-existing walker behaviour shared with digit-boundary names. Named gap for Worker-0 to route
  to an `optimizer/walker.py` Performance review (out of this run's scope): ~50x per-selection
  cost on the miss path, paid per plan build (plan-cache miss, every non-cacheable request);
  candidates to measure there are a per-type memo of the forward name map or a raw
  `field_map.get(graphql_name)` probe before the scan. Reopens here only if the walker item shows
  the miss path above 2% of `bench_optimizer_walk.py` time on a supported schema.

Cells: default only. Sharded and pg `inapplicable by construction`, judged and upheld for L1 (pure
`str -> str`, no connection, alias or dialect); M1's cells are the Mechanics verifier's to judge.

Disputes: none in `## Implementation (Worker-2)` for this axis. Cross-axis findings placed here:
none. The Performance record's out-of-axis `snake_case.__doc__` lead landed as Comments F2 (graded
by the Comments verifier).

Verdict: L1 verified; no new Performance finding on this item.

Fingerprints (`git hash-object`, shared tree, all equal to Worker-2's): `utils/strings.py`
536d175cd605; `optimizer/walker.py` 73d6929a5881; `types/base.py` 49057fad2058;
`types/finalizer.py` de34ae2aaed1; `management/commands/inspect_django_type.py` 2807d0fc9d75;
`tests/utils/test_strings.py` 3dad1a9d42d8; `tests/optimizer/test_extension.py` 4101bbd3805e;
`scripts/bench_optimizer_walk.py` de745175799b; probe `performance/probe_plain_text.py`
d239152c6bc4; `diff/pass-1.diff` b8c938472fac.

Handoff: Read beyond the record: the walker's `_resolve_selection_target`,
`_field_by_graphql_name`, `_graphql_names_by_python_name` bodies (the miss path), Worker-2's
`proofs.json` and before/after JSON, the whole diff. The only open thread is the walker miss-path
cost above, which belongs to `optimizer/walker.py`, not this item; with a converter in `info` it
will be higher than the `info=None` figure measured here (one `converter.get_graphql_name` per
Strawberry field per miss). The walk bench on this machine swung ~15% between identical runs, so
a later pass comparing walk figures should interleave copies as done here rather than compare to
the baseline table. The miss probe's source is kept under `verify-performance-1/`; its copy under
`tests/optimizer/test_zz_probe_miss.py` lives only in slot-3.
