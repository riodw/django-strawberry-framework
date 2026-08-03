# Build: Review round R1b — expression-owned bound-payload retention

Spec reference: `docs/spec-045-visibility_boundary-0_0_14.md` (Decision 8, `## Error shapes`, `## Constraints on the supported query surface`)
Status: built

## Plan (Worker 1)

There was no separate Worker 1 planning pass for this round: Worker 0 dispatched the
research-and-fix directly on the maintainer's decision (build plan
`docs/builder/build-045-visibility_boundary-0_0_14.md`, R1b bullet). The plan's substance
— the shape enumeration, the verdict per shape, the rejected alternatives, and the
single-home DRY argument — is recorded in the build report below, per the dispatch
instruction. The maintainer's decision and its two binding constraints: fix the root
cause; do NOT duplicate functions another package already provides; where the limitation
genuinely belongs to another package, cap the contract there (naming an actual upstream
bug explicitly if one is found).

### Dispatched findings checklist

- [x] An expression-owned bound payload escapes Decision 8's ownership invariant:
      `::_expr_graph_defect` reaches children through `get_source_expressions()`, which a
      `Value` answers `[]`, so `Value.value` is never visited; `::_reconstructed_value`
      routes that slot to `::_normalized_bound_value`, whose `for … else` returned
      UNCHANGED anything descending from no `_BOUND_VALUE_NORMALIZERS` entry and not an
      `enum.Enum`. Probed at HEAD: `Category.objects.filter(is_private=False)
      .annotate(probe=Value(<arbitrary object>))` sealed with `defect: None` and the
      sealed payload `is` the candidate's object; a `list` subclass was likewise retained
      with a post-seal `append` observable inside the sealed query
      (`docs/builder/temp-tests/r1/probe_mutable_container_retention.py`).
      `::_direct_rhs_defect` rejects exactly this shape on a `Lookup`'s right-hand side,
      so the boundary applied its own admitted-bound-value rule inconsistently by slot
      position — the asymmetry, not the dispatch site, is the root cause.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short`: `M django_strawberry_framework/utils/querysets.py`,
`M tests/utils/test_querysets.py`, plus this artifact and
`docs/builder/temp-tests/r1b/proofs.json`. Also dirty but NOT this pass's work (baseline
concurrent files, untouched): `docs/feedback.md` (maintainer session),
`docs/spec-045-visibility_boundary-0_0_14.md` + `-rationale.md` +
`docs/builder/bld-045-r1-rationale_reconciliation.md` +
`docs/builder/build-045-visibility_boundary-0_0_14.md` (R1 / Worker 0 output).

- `django_strawberry_framework/utils/querysets.py` — the fix (below).
- `tests/utils/test_querysets.py` — 12 new tests, 2 re-pinned (details below).

### The fix, and why its home is single

The admitted-bound-value rule already had one home split across two halves:
`::_direct_rhs_defect` (walk-time admission for the one slot the walk can see) and
`::_normalized_bound_value` (reconstruction-time normalization for every slot). The
defect was that `::_normalized_bound_value`'s fallback was **fail-open** — the exact
fail-open shape `BUILD.md` names (a default reached because the input was unclassifiable
rather than trusted). Payload slots are unenumerable (any genuine expression may keep
bound state in an ordinary instance slot the walk's accessors never surface), so the only
place every retained object is decided is canonical reconstruction, and
`::_normalized_bound_value` is the one function every non-node, non-container leaf
reaches there. The fix closes the fallback **at that single home**:

1. `::_normalized_bound_value` now fails closed (`spec-045` Decision 8): a bound payload
   that neither reduces to an exact inert value, nor is trusted schema
   (`::_RETAINED_SCHEMA_BASES` — classes, `models.Field`, `ForeignObjectRel`,
   `models.Model` instances), nor is an enum member reducible through its `_value_`,
   raises `::_UntrustedBoundValueError`. The pre-existing post-normalization inert check
   raises the same marker. This guards the ANSWER ("is this payload proven inert or
   proven trusted?"), not a spelling — no slot name, no expression class, no `Value`
   special case appears anywhere in the fix.
2. `::_reconstruction_defect` catches the marker class first and reports a typed
   `untrusted` defect naming the payload's type (`"<QuerySet> binds a <Type> bound
   value"`); every other reconstruction exception keeps the generic wording. A marker
   class, not message matching.
3. `::_reconstructed_value`'s dict rebuild now applies the identical
   retain-or-reconstruct rule to mapping KEYS (previously carried by reference), because
   a rebuilt mapping keeping a consumer key by reference is the same ownership violation
   one slot over.
4. Two deliberate admissions the sweep proved necessary (they are ordinary consumer
   state the old fail-open silently passed):
   - exact `datetime.timezone` / `zoneinfo.ZoneInfo` join `::_RETAINED_LEAF_TYPES` —
     `Trunc(..., tzinfo=...)` / `Extract(..., tzinfo=...)` keep the object on an ordinary
     instance slot; both types are immutable, stdlib-owned, and `datetime.timezone` is
     not subclassable, so exact-type retention is airtight;
   - `ForeignObjectRel` joins the retained schema bases — a reverse-relation
     `Join.join_field` is the reverse side of the model's own field and its state
     legitimately carries the model's own callables (`django.db.models.deletion.CASCADE`
     on `on_delete`, found by the full sweep the moment the fallback closed). Previously
     these rel objects were rebuilt with their function members flowing through the
     fail-open path; retention matches the `models.Field` rationale exactly.
5. `::_RETAINED_SCHEMA_BASES` names the schema trio-now-quartet ONCE, consumed by both
   `::_is_reconstructable_node` and `::_normalized_bound_value`, so the
   rebuild-versus-retain policy and the bound-value rule cannot drift (the DRY answer to
   "the rule needs the predicate in two places").

No upstream function was re-implemented: normalization keeps using the base types' own
descriptors and C slots (unchanged), reconstruction keeps `object.__new__` + validated
state transfer (unchanged), and no copying/adaptation primitive was written.

### Shapes enumerated, verdict per shape, reason

Enumerated against Django 6.0.5 (shared venv) sources (`expressions.py`, `functions/`,
`lookups.py`, `aggregates.py`, reverse_related) plus the full-sweep empirical check
(5298-test run exercises the seal through every fakeshop surface):

| Shape | Verdict | Reason |
|---|---|---|
| `Value.value` = opaque consumer object | **refused** (`untrusted`, type named) | neither inert nor trusted schema; was retained by reference at HEAD |
| `Value.value` = `list` / `dict` subclass | **refused** | consumer-owned methods + observable post-seal mutation; the direct-RHS rule already refuses the shape |
| `Value.value` = exact plain `dict` / `list` / `tuple` / `set` | **admitted, rebuilt member-wise** | legitimate JSON/array-shaped payload; already rebuilt at HEAD, now pinned |
| `Value.value` = plain-data subclass (`TextChoices` member, date subclass) | **admitted, normalized to exact base** | same replacement a direct RHS gets; already normalized at HEAD, now pinned in payload position |
| mapping KEY in any rebuilt payload dict | **same rule as values** | a retained consumer key is the same shared-mutable violation; JSON encoders also dispatch `str()` on non-str keys at compile |
| `Trunc` / `Extract` `.tzinfo` = exact `datetime.timezone` / `zoneinfo.ZoneInfo` | **admitted, retained by reference** | ordinary consumer annotation; immutable stdlib values, every method interpreter-owned; `datetime.timezone` unsubclassable |
| `.tzinfo` = consumer `tzinfo` subclass, `dateutil` tz | **refused** — cap at the other package | no descriptor-only way to rebuild one; consumers use stdlib zoneinfo (Django ≥5 dropped pytz support, so pytz is dead at the floor) |
| `ForeignObjectRel` (reverse `join_field`) | **retained: trusted schema** | reverse side of the model's own field; carries the model's own `on_delete` / `limit_choices_to` callables, which are schema, not a bound payload |
| enum member with unreducible `_value_` (opaque object, model instance) | **refused, member type named** | reduces to no framework-owned parameter (the model-value case newly exercises the post-normalization inert check) |
| psycopg `Json` wrapper, `django.contrib.postgres` `Range`, `memoryview` | **refused** — cap at the other package / consistent contract | the direct-RHS rule already refused all three at HEAD; the fix makes the payload slot agree rather than widening. A consumer expresses ranges/JSON via genuine primitives and plain data |
| `Lookup.rhs`, `RawSQL.params` / `ExtraWhere`, `Func.extra`, `_SQL_TEMPLATE_ATTRS`, sequence-state attrs | **unchanged** | already validated at walk time by their existing rules; reconstruction-time enforcement now backstops them generically |

**Upstream bug check:** none found. Nothing was added to `_django_patches.py` /
`_strawberry_patches.py`. The two caps above (third-party tzinfo implementations;
psycopg/postgres value wrappers) are other packages' opaque value types, not bugs —
recorded as deliberate contract caps consistent with the spec's existing
"consumer-defined expressions and lookups are unsupported" constraint.

### Rejected alternatives

- **Enumerate payload slots in the walk** (`Value.value`, `tzinfo`, `Collate.collation`,
  …): per-class slot lists are the whack-a-mole Decision 8 argues against — every Django
  release can add a slot, and a missed sibling reproduces the defect. Rejected.
- **A parallel validator beside `_direct_rhs_defect`** running over payload slots at walk
  time: duplicates the admitted-bound-value rule in a second home (the dispatch named
  this a finding, not a fix) and still requires the slot enumeration above. Rejected.
- **Widen `_INERT_VALUE_TYPES` with the tzinfo types**: would widen walk-time admission
  everywhere (direct RHS, raw-SQL params) for types only meaningful in timezone position;
  the retention-only admission (`_RETAINED_LEAF_TYPES`) is the narrower surface. Rejected.
- **`copy.deepcopy` unknown payloads instead of refusing**: the upstream copying
  primitive exists but dispatches a consumer `__deepcopy__` / `__reduce__` mid-seal —
  Decision 8 already rejects it for reconstruction; refusal is the cap the maintainer's
  constraint 2 prescribes. Rejected.
- **Match the refusal by exception message text** instead of a marker class: brittle;
  `_UntrustedBoundValueError(TypeError)` distinguishes the deliberate refusal from an
  incidental re-hash failure structurally. Rejected.
- **Keep rebuilding `ForeignObjectRel` with a provenance carve-out for its function
  members** ("a genuine module-level Django function is fine"): rebuilding schema was
  never the invariant's aim, a function-provenance rule is new validation surface, and
  retention matches the existing `models.Field` treatment byte-for-byte in rationale.
  Rejected.

### Tests added or updated

Added (all `tests/utils/test_querysets.py`):

- `test_value_payload_opaque_object_fails_closed` — the reported instance; also pins that
  the candidate keeps its own payload (seal never mutates the candidate).
- `test_value_payload_mutable_container_subclass_fails_closed` — list + dict subclass.
- `test_value_payload_plain_containers_rebuild_without_sharing` — exact dict/list
  admitted; equal, NOT identical; post-seal candidate mutation invisible in the sealed
  query; non-str inert mapping key admitted.
- `test_value_payload_plain_data_subclass_normalizes_to_exact_value` — `TextChoices` /
  date subclass in payload position → exact base, override never fired, candidate keeps
  its instances.
- `test_value_payload_mapping_key_plain_data_subclass_normalizes`,
  `test_value_payload_mapping_key_enum_member_normalizes` — the key channel's admission
  direction.
- `test_reconstruction_hostile_mapping_key_fails_closed` — the key channel's refusal.
- `test_value_payload_field_instance_is_retained_schema` — fresh local `models.Field`
  subclass instance retained by identity (fresh class = deterministic first-encounter
  coverage of the schema-retain branch, independent of the `_RETAINED_TYPES` memo).
- `test_enum_member_with_model_value_fails_closed` — the post-normalization inert check's
  raise, member type named.
- `test_hostile_tzinfo_subclass_fails_closed` — a non-`Value` payload slot (`tzinfo`),
  proving the rule guards the answer, not the `Value` spelling.
- `test_trunc_tzinfo_is_retained_and_rows_survive` (django_db) — `ZoneInfo` +
  `datetime.timezone.utc` retained by identity AND rows returned.
- `test_value_payload_literals_seal_and_rows_survive` (django_db) — `Value(1)` /
  `Value("x")` seal and return rows with the annotation values intact.

Re-pinned (both in this pass's ownership):

- `test_lookup_direct_rhs_unnormalizable_enum_member_fails_closed` — detail is now the
  typed `"QuerySet binds a _OpaqueValue bound value"` instead of the generic
  reconstruction wording (the refusal moved from the post-check to the fallback).
- `test_query_state_that_cannot_be_reconstructed_fails_closed_typed` — its old `_ArmedKey`
  mechanism now trips the bound-value rule first (keys are validated), so the generic
  `except Exception` branch is re-pinned via a hollow `uuid.UUID` subclass (allocated past
  `__init__`, admitted on ancestry, whose normalizer's base-slot read raises) — an
  incidental failure that keeps the generic wording.

Row-survival direction beyond the file: the full sweep (below) runs every fakeshop live
query through the seal; the floor run re-executed `tests/test_connection.py`,
`tests/test_relay_node_field.py`, `tests/test_list_field.py`.

### Validation run

- `uv run ruff format django_strawberry_framework/utils/querysets.py tests/utils/test_querysets.py` — pass (no changes).
- `uv run ruff check --fix <same files>` — pass.
- `uv run python scripts/check_trailing_commas.py <same files>` — pass.
- `git status --short` — modified files classified under `### Files touched`; everything
  outside this pass's ownership is baseline concurrent work, untouched.
- Focused: `uv run pytest tests/utils/test_querysets.py --no-cov` — 249 passed.
- Full sweep: `uv run pytest --no-cov` — **5298 passed, 40 skipped** (run because the
  fail-closed rule could plausibly refuse a legitimate shape anywhere the seal runs; it
  is what surfaced the `ForeignObjectRel` `on_delete` function and forced the schema-
  retention decision instead of shipping a fix that fail-closed every reverse-relation
  join).

### Failability proofs

Procedure, mechanized by `scripts/prove_failability.py` (manifest
`docs/builder/temp-tests/r1b/proofs.json`, scratch root outside the repo, exit code 0):
the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation
site is located by an exact anchor asserted to match exactly once; the same focused scope
is run unmutated first, so rows already failing before the mutation are differenced out;
both runs use `--no-cov`; the file is restored from the pre-mutation copy and the restore
proved by `filecmp.cmp(shallow=False)` plus SHA-256 comparison. One boundary at a time,
restored before the next. `git` never invoked.

1. `django_strawberry_framework/utils/querysets.py::_normalized_bound_value`
   - Mutation applied: the fail-closed fallback
     `if not issubclass(value_type, enum.Enum): raise _UntrustedBoundValueError(...)`
     replaced by the fail-open `if not issubclass(value_type, enum.Enum): return value`
     (retain by reference) — the boundary removed, not perturbed.
   - Scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py`
   - Pre-mutation state of that scope: `249 passed` (exit 0); pre-existing failing rows
     differenced out: 0.
   - Failing node ids (count = len of this list = **5**):
     - `tests/utils/test_querysets.py::test_lookup_direct_rhs_unnormalizable_enum_member_fails_closed`
     - `tests/utils/test_querysets.py::test_reconstruction_hostile_mapping_key_fails_closed`
     - `tests/utils/test_querysets.py::test_value_payload_opaque_object_fails_closed`
     - `tests/utils/test_querysets.py::test_value_payload_mutable_container_subclass_fails_closed`
     - `tests/utils/test_querysets.py::test_hostile_tzinfo_subclass_fails_closed`
   - Collection/setup errors: **0**.
   - Revert proved by byte-comparison: `filecmp.cmp(shallow=False)` True; sha256
     `43fccff93602b0ab...` == `43fccff93602b0ab...` (vs pre-mutation copy).

2. `django_strawberry_framework/utils/querysets.py::_reconstructed_value` (dict-rebuild
   key rule)
   - Mutation applied: the two key-rule lines
     `if not (key is None or type(key) in _RETAINED_TYPES): key = _reconstructed_value(key, memo)`
     deleted, so every mapping key is carried into the sealed query by reference.
   - Scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/utils/test_querysets.py`
   - Pre-mutation state of that scope: `249 passed` (exit 0); pre-existing failing rows
     differenced out: 0.
   - Failing node ids (count = **3**):
     - `tests/utils/test_querysets.py::test_reconstruction_hostile_mapping_key_fails_closed`
     - `tests/utils/test_querysets.py::test_value_payload_mapping_key_plain_data_subclass_normalizes`
     - `tests/utils/test_querysets.py::test_value_payload_mapping_key_enum_member_normalizes`
   - Collection/setup errors: **0**.
   - Revert proved by byte-comparison: `filecmp.cmp(shallow=False)` True; sha256
     `43fccff93602b0ab...` == `43fccff93602b0ab...` (vs pre-mutation copy).

No zero-row entries. Boundary 2 sits at 3 rows, inside Worker 3's mandatory re-run floor.
The post-normalization inert check (`if not _is_inert_value(normalized): raise …`) is a
pre-existing boundary (formerly a bare `TypeError`), not a new one, so it carries no
proof; it is pinned by `test_enum_member_with_model_value_fails_closed` and the
re-pinned enum test. The tzinfo / `ForeignObjectRel` retentions are admissions, not
rejection paths; their guarantees are pinned by the row-survival and identity assertions.

### Hot-path budget

Metric: median wall-clock per `_seal_or_defect` call (µs), median of 5 batches x 2000
iterations each, three query shapes (simple filter; filter+annotation+order; annotation-
heavy Case/Concat/Trunc), measured on the same machine before and after the change.
Snippet: `scratchpad/bench_seal.py` (reproduced under `### Notes for Worker 3`); command:
`DJANGO_SETTINGS_MODULE=config.test_settings PYTHONPATH=examples/fakeshop uv run python bench_seal.py`.

| Shape | Before | After | Delta |
|---|---|---|---|
| simple | 20.14 µs | 19.99 µs | -0.7% |
| medium | 34.51 µs | 33.62 µs | -2.6% |
| annotation-heavy | 80.09 µs | 78.28 µs | -2.3% |

Neutral to slightly faster: the added per-leaf work is one `issubclass` on the rare
subclass path, while retaining `ForeignObjectRel` by reference removes a whole
object-rebuild per reverse-relation join. Acceptability is the maintainer's call; the
numbers exist next to the change.

### Floor verification

Owned by this pass per the plan's declaration.

- Scratch venv: `/tmp/dsf-floor-045` (outside the repo), built per `BUILD.md`
  `### How to build the floor venv`.
- Resolved versions (`uv pip list --python /tmp/dsf-floor-045/bin/python`): Python
  3.10.19, `django 5.2` (== 5.2.0), `strawberry-graphql 0.316.0`, `asgiref 3.12.1`.
- `/tmp/dsf-floor-045/bin/python -m pytest tests/utils/test_querysets.py --no-cov` —
  **249 passed** (pass).
- `/tmp/dsf-floor-045/bin/python -m pytest tests/test_connection.py
  tests/test_relay_node_field.py tests/test_list_field.py --no-cov` — **144 passed**
  (pass).

Floor-relevant facts executed, not read: `uuid.UUID` is slotted at 3.10 (the hollow-UUID
generic-branch test passes at the floor), `zoneinfo` is stdlib at 3.10, and Django 5.2.0
stores `Trunc.tzinfo` / `ManyToOneRel.on_delete` in the same slots as 6.0.5.

### Implementation notes

- `_UntrustedBoundValueError(TypeError)`: a marker subclass so `_reconstruction_defect`
  distinguishes the deliberate refusal (typed detail naming the payload type — the
  consumer can find the offending `Value(...)`) from an incidental failure (generic
  wording) without message matching. `TypeError` base keeps any hypothetical broad
  `except TypeError` in callers semantically unchanged.
- The `_normalized_bound_value` head guard returns exact `_RETAINED_LEAF_TYPES` members
  unchanged — needed because the enum `_value_` recursion is the one caller that can hand
  the function an exact leaf (e.g. `_value_ = None`); `bytearray` is deliberately NOT in
  that set, so an exact one still routes to its copying normalizer rather than being
  shared by reference.
- The dict rebuild switched from a comprehension to a loop: the key rule made the
  comprehension unreadable; per-element cost is unchanged in shape.
- The `_RETAINED_LEAF_TYPES` widening is expressed as a set union on
  `_INERT_VALUE_TYPES - {bytearray}` so the tzinfo admission is visibly
  reconstruction-scoped: `_INERT_VALUE_TYPES` (walk-time admission) is untouched.

### Notes for Worker 3

- Repro probes: `docs/builder/temp-tests/r1/probe_value_retention.py` and
  `probe_mutable_container_retention.py` now print `('untrusted', 'QuerySet binds a
  Hostile bound value')` / `('untrusted', 'QuerySet binds a HostileList bound value')`
  and the plain-dict contrast case still seals with a rebuilt (non-identical) dict.
- Shadow output refreshed post-change:
  `docs/shadow/django_strawberry_framework__utils__querysets.overview.md` /
  `.stripped.py` (line numbers not canonical).
- Proof manifest for independent re-run: `docs/builder/temp-tests/r1b/proofs.json`
  (`--only 1` / `--only 2`); boundary 2 is at 3 rows, inside your mandatory floor.
- Hot-path bench snippet (also on disk in the session scratchpad as `bench_seal.py`):
  builds the three shapes above, calls `str(qs.query)` once outside the timed loop,
  asserts a clean seal, then times `_seal_or_defect(qs, Category, None)` over 5x2000
  iterations per shape and prints the median. Shapes: `simple` =
  `Category.objects.filter(is_private=False)`; `medium` = same + `name__icontains`
  filter + `Value(1)` annotation + `order_by`; `annotation_heavy` = Case/When +
  Concat + `Trunc("created_date", "day")` + `order_by`.
- The `except ImportError` guard on `PROHIBITED_FILTER_KWARGS` and everything else in the
  module is untouched; the diff is confined to the reconstruction/normalization block and
  imports.

### Notes for Worker 1 (spec reconciliation)

The fix closes a retention the spec currently RECORDS as open, so Decision 8 and the
constraints section must be amended. Each amendment: location, current wording, and the
recommended replacement.

- **Where:** `### Decision 8 …`, subsection "**What the sealed query still shares with
  the candidate, exhaustively.**", fourth bullet.
  **Current wording (quoted):** "a bound-value slot the graph proofs do not route through
  the direct-lookup rule — an expression's own plain-data payload, `Value.value` being
  the instance. A `Value`'s `get_source_expressions()` returns no children, so the walk
  never reaches that slot, and normalization replaces only a value descending from a
  plain-data base; anything else in it is retained by reference. Reaching this requires
  binding a non-plain-data object into an expression payload, which is a crafted-object
  path and therefore out of scope above; the value is bound as a `%s` parameter and
  cannot alter SQL structure. It is recorded here rather than claimed closed."
  **Recommended replacement:** delete this bullet, and extend the remaining shared list
  with two entries: "exact stdlib timezone objects — `datetime.timezone` (not
  subclassable) and exact `zoneinfo.ZoneInfo` — carried by a genuine `Trunc` / `Extract`,
  immutable values whose every method is the interpreter's own;" and "`ForeignObjectRel`
  relation descriptors (a reverse-relation `Join.join_field`), the reverse side of the
  model's own fields, whose state legitimately carries the model's own callables
  (`on_delete`)." Then state the closed contract: "An expression-owned bound payload the
  graph proofs do not route through the direct-lookup rule — `Value.value` being the
  instance — obeys the SAME admitted-bound-value rule at reconstruction: an exact inert
  leaf or exact plain container is admitted (containers rebuilt member-wise, mapping keys
  under the same rule as values), a plain-data subclass is normalized to an exact inert
  value, trusted schema is retained, and anything else fails closed as an `untrusted`
  defect naming the payload's type (`_normalized_bound_value` /
  `_UntrustedBoundValueError`). The rule has one home, so the verdict cannot vary with
  where the value sits."
- **Where:** `## Constraints on the supported query surface`, third bullet.
  **Current wording (quoted):** "**One bound-value slot is retained rather than
  normalized** — an expression's own plain-data payload, `Value.value` being the
  instance — for the reasons and with the bounds Decision 8 records."
  **Recommended replacement:** delete the bullet (the retention no longer exists), or
  replace with: "**Opaque bound payloads are unsupported across the boundary** — a bound
  value that neither reduces to an exact inert value nor is trusted schema (a psycopg
  `Json` wrapper, a postgres `Range`, a `memoryview`, a third-party `tzinfo`
  implementation) fails closed as `untrusted`; consumers bind plain data or exact stdlib
  values. Exact `datetime.timezone` / `zoneinfo.ZoneInfo` are supported."
- **Where:** `### Decision 8 …` "**Enforcing symbols.**"
  **Current wording (quoted, fragment):** "[`::_normalized_bound_value`][querysets] and
  `::_BOUND_VALUE_NORMALIZERS` (exact-value normalization through base-type
  descriptors);"
  **Recommended replacement:** extend to "… (exact-value normalization through base-type
  descriptors, and the fail-closed bound-value rule: `::_UntrustedBoundValueError`,
  `::_RETAINED_SCHEMA_BASES`, `::_RETAINED_LEAF_TYPES`);".
- **Where:** `### Decision 8 …` "**Tests that pin it.**"
  **Current wording (quoted, fragment):** "…
  `test_lookup_direct_rhs_attribute_hook_never_dispatches`, and
  `test_func_extra_template_parameter_object_fails_closed`."
  **Recommended replacement:** append the payload-position pins:
  `test_value_payload_opaque_object_fails_closed`,
  `test_value_payload_mutable_container_subclass_fails_closed`,
  `test_value_payload_plain_containers_rebuild_without_sharing`,
  `test_value_payload_plain_data_subclass_normalizes_to_exact_value`,
  `test_reconstruction_hostile_mapping_key_fails_closed`,
  `test_hostile_tzinfo_subclass_fails_closed`, and
  `test_trunc_tzinfo_is_retained_and_rows_survive`.
- **Where:** `## Error shapes`, `untrusted` row, "Fails when" column.
  **Current wording (quoted):** "foreign `Query` class, foreign row iterable, unresolved
  deferred filter, unsealable prefetch child"
  **Recommended replacement:** "foreign `Query` class, foreign row iterable, unresolved
  deferred filter, unsealable prefetch child, or a bound payload that is neither inert
  plain data nor trusted schema". No new defect code was introduced; the rejection reuses
  `untrusted` with its existing consumer-facing wording (the type-named detail rides the
  `({detail})` slot the wording already carries).
- **Hot-path declaration reconciliation:** the plan's R1b hot-path obligation is
  discharged with a neutral-to-negative delta (table above); no spec cost sentence needs
  changing (Decision 8's "Cost" paragraph describes reconstruction overall and still
  holds).

---
