# Build: Superseded close-cycle review — historical pre-candidate snapshot

Spec reference: `docs/spec-050-list_field_arguments-0_0_15.md` — Decision 20 (the admission rule),
Decision 22 (the close sequence), Decision 8, Decisions 14-21, and `## Definition of done` (cited
by heading; the line ranges first recorded here matched no committed tree). Admission rule also `AGENTS.md`
rule 35 and `GOAL.md` `## Trust boundary`.
Status: superseded historical review (accepted only for its pre-candidate snapshot)

Superseded, not evidence. The measurements below describe the pre-candidate snapshot
`20646db2` plus working-tree paths. The gated candidate is `2c66416e` (tree `5ce4c799`) and the
evidence-only follow-up is `b38184b3`; the gate and the Decision 20 review of that exact tree are in
`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` `## Closing record`. Working-tree
measurements (digests, md5s, sweep counts) are not reproducible from any commit.

This artifact is not the Decision 22 gate. Its tree identifiers and measurements describe a
pre-candidate snapshot that the current WIP checkout no longer is; the candidate commit and the
evidence-only follow-up are recorded at `2c66416e` / `b38184b3`.

## Review (Worker 3)

This is the historical draft of the single review Decision 22 step 4 requires, not a cohort
re-review and not the final gate. Both cohort artifacts (`docs/builder/bld-050-close-row_carry.md`,
`docs/builder/bld-050-close-trust_docs.md`) are `final-accepted`; this pass reads the assembled
tree as one object against the `## Definition of done` and grades every candidate finding against
Decision 20's three conditions in writing.

### Historical pre-candidate snapshot (not current evidence)

The review snapshot was `HEAD` `20646db2` plus sixteen working-tree paths. That identifier is
superseded and is retained only to identify the historical run. Every other dirty path in that
snapshot was a concurrent session's and was neither read as the card's nor touched. Per-path
`git diff HEAD --numstat`, measured at that historical review:

| Path | ins/del |
|---|---|
| `django_strawberry_framework/permissions.py` | 1/1 |
| `django_strawberry_framework/resource_policy.py` | 27/16 |
| `django_strawberry_framework/schema.py` | 9/6 |
| `django_strawberry_framework/types/resolvers.py` | 3/3 |
| `django_strawberry_framework/utils/querysets.py` | 92/35 |
| `docs/README.md` | 29/9 |
| `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` | 74/0 |
| `docs/spec-050-list_field_arguments-0_0_15.md` | 163/47 |
| `docs/spec-050-list_field_arguments-0_0_15-rationale.md` | 69/2 |
| `examples/fakeshop/test_query/test_list_field_api.py` | 10/7 |
| `examples/fakeshop/test_query/test_list_field_async_api.py` | 6/4 |
| `examples/fakeshop/test_query/test_resource_policy_api.py` | 215/2 |
| `tests/test_resource_policy.py` | 208/5 |
| `tests/utils/test_querysets.py` | 149/10 |
| `docs/builder/bld-050-close-row_carry.md` | new |
| `docs/builder/bld-050-close-trust_docs.md` | new |

Four of those numbers are the figures the two cohorts' final verifications were written against
(`tests/test_resource_policy.py` 208/5, `resource_policy.py` 27/16, `docs/README.md` 29/9,
`schema.py` 9/6), so the tree under review is the tree those verifications accepted and nothing
had been edited into it since. Tracked `examples/fakeshop/db.sqlite3` md5
`2732e633f3303c55aac9d9f398e48df7` before and after every command in that historical pass;
its snapshot `HEAD` was `20646db2` throughout. No tracked file was written by that review.

### Every candidate finding, against Decision 20's three conditions

Conditions, written out per row: **(a)** the Definition-of-done row it breaks, quoted; **(b)** a
project shape that could feasibly exist under supported public API, stated as code a project would
write; **(c)** the wire or configuration input that reaches it.

#### C1 — the retired "unresolved deferred filter" vocabulary survives at four first-party sites

**(a) FAILS.** No `## Definition of done` row states the cause enumeration inside the seal's
`untrusted` message or the `utils/querysets.py` module docstring. The row that is nearest —

> - [ ] No raw-list row source decides its own ceiling. ... A pending reverse-relation predicate
>   does not make a subclass unrebuildable: Django leaves one on every relation queryset it builds
>   whatever class the manager was made from, and the seal bakes it onto the detached clone through
>   the unbound `Query.add_q` for every candidate, while a deferred-filter state that is not the
>   exact shape Django writes - the `negate` slot's exact `bool` included, proven not to reach its
>   own `__bool__` - is refused with that same typed error. Sealability does not depend on which
>   surface seals.

— is a statement about what the seal DOES, and the code does exactly that (proven below). What is
stale is prose describing the retired rule, which no row owns.

**(b) HOLDS.**

```python
class MyUpper(models.Func):        # ordinary public Django API
    function = "UPPER"

class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name")

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.annotate(u=MyUpper(models.F("name")))
```

**(c) HOLDS.** Any query selecting that type, under the pass-through error policy. Measured
(`docs/builder/temp-tests/050/final/probe_message.py`, run against `Category`, not the `Item`
shown above): the seal answers
`('untrusted', "annotation 'u' carries a MyUpper node")` and `_visibility_result_error` renders

> `_T.get_queryset returned a queryset that cannot be sealed into a framework-owned execution
> queryset (annotation 'u' carries a MyUpper node); the visibility boundary rebuilds a plain
> QuerySet from the validated query state, and a foreign Query class, a foreign row iterable, or an
> unresolved deferred filter cannot be faithfully rebuilt. ...`

— naming, as a cause, a state that is no longer a defect at all.

**NOT ADMITTED** (condition (a)). Recorded as a new-card candidate below. Measured by a per-line grep,
which misses wrapped sites: occurrences of `unresolved deferred` in tracked `.py`, **12 at HEAD → 3
now**. A line-joining reader gives 13→4; the fourth survivor is `permissions.py:369-370`,
`_root_error_renderer`'s `untrusted` message. All four were fixed in `f7192bfb`. The three
per-line survivors are

- `django_strawberry_framework/permissions.py:432` — the cascade's `untrusted` wire message. The
  docstring of that same function (`_edge_error_renderer`, line 400) IS changed to `malformed` by
  this diff, so the function's docstring now describes its own message wrongly, one screen apart.
- `django_strawberry_framework/utils/querysets.py:3651` — `_visibility_result_error`'s `untrusted`
  message. Its sibling site `_prepared_visibility_source` (line ~3781) WAS changed to `malformed`
  by this diff, so the two visibility message sites Decision 5 keeps in step now disagree.
- `django_strawberry_framework/utils/querysets.py:54` — the module docstring: "a foreign `Query`
  class, a foreign row-iterable class, or an unresolved deferred filter cannot be faithfully
  rebuilt, so they fail closed (`untrusted`)". False as of this diff.

Fix hypothesis if a card takes it: replace `unresolved` with `malformed` at all four, matching the
wording already landed at the four sibling sites.

#### C2 — the new `_result_cache` shape check emits `untrusted` after the `routing` check

**(a) FAILS** — no DoD row fixes the seal's internal code ordering; the ordering claim lives in
Decision 5 ("`type`, `table`, `untrusted`, `routing`, `evaluated`, `sliced`, `combined`,
`projection`, `alias`", with the rationale "every trust-family proof still runs first").
**(c) FAILS** — no input reaches both checks: `expected_routing` is supplied only by the
post-`OrderSet` result seal (`_ORDERSET_RESULT_POLICY` (now `_SIDECAR_RESULT_POLICY`)), and `carry_result_cache` is set only by
`_RAW_LIST_SOURCE_POLICY`, which `normalized_row_source` calls with `required_alias=None` and no
`expected_routing`. The two defects cannot co-occur, so no ordering is observable.
**NOT ADMITTED.** Robustness note only.

#### C3 — the exact-`list` `_result_cache` refusal is not reachable through supported public API

**(a) FAILS**, **(b) FAILS.** Django writes an exact `list` into `_result_cache` at every site that
populates it (`QuerySet._fetch_all` → `list(self._iterable_class(self))`, and
`prefetch_one_level` → `qs._result_cache = vals`; also `RawQuerySet._fetch_all`, and
`Prefetch.__getstate__`, which writes `[]`), so no project using supported API produces
another shape. **NOT ADMITTED** — it is a fail-closed typed error kept for the reason Decision 20
keeps cheap robustness rows, and it is correctly `type(...) is list` rather than `isinstance`.

#### C4 — `_SealPolicy` does not enforce its own "no policy sets both" sentence

`carry_result_cache`'s docstring says "It is the complement of `require_unevaluated`, and no policy
sets both", and nothing in the dataclass refuses the combination. **(a) FAILS** (no DoD row),
**(c) FAILS** (no shipped policy sets both; a future one would be package code, not wire or
configuration input). Behavior is defined if it ever happens — the carry's shape check runs first,
then `require_unevaluated` refuses — so the outcome is a refusal, not a leak. **NOT ADMITTED.**

### Admitted findings

**No finding admitted under Decision 20.** Four candidates were written out above and each fails at
least one condition; none re-loops the gate.

### High:

None.

### Medium:

None.

### Low:

- **C1**, the three per-line surviving `unresolved deferred filter` sites (four by a line-joining
  reader; all fixed in `f7192bfb`). Low by `BUILD.md`'s tiers
  (docstrings stale or wrong but not load-bearing) for `utils/querysets.py:54`; the two message
  sites are remediation advice a schema author reads, so they are the part worth a card. Not
  admitted; not a blocker.
- **C2**, **C4**: one-sentence notes, no action required.

### What I verified, and how

- **The behavioral rows the cycle amended are true of the code.**
  - `carry_result_cache` reaches exactly one policy: `_RAW_LIST_SOURCE_POLICY`, used at exactly one
    call site (`utils/querysets.py:3447`, inside `normalized_row_source`). Grepped the whole module
    for `_SealPolicy(` constructions and every `policy=` argument; no other seal can receive it, so
    `_prepared_visibility_source`'s amended claim ("this seal's policies do not carry
    `_result_cache` forward") is true by construction rather than by convention.
  - `require_unevaluated` reaches exactly one policy (`_ORDERSET_RESULT_POLICY` (now `_SIDECAR_RESULT_POLICY`)), which is what
    Decision 8's amended paragraph asserts.
  - The carried rows cannot escape the ceiling: `_windowed_rows` normalizes first, then dispatches
    on `type(result) in _SLICE_BOUNDED_ROW_TYPES`; the sealed rebuild is an exact
    `models.QuerySet`, and `QuerySet.__getitem__` on a populated cache answers
    `self._result_cache[k]`, which is the interpreter's own `list` subscript because the seal
    refuses every non-`list` cache it carries. The zero-width arm (`result[start:start]`) takes the
    same route.
  - The window never re-runs a prefetch on carried rows: `__getitem__` returns from the cache
    without reaching `_fetch_all`, which is the only place `_prefetch_related_objects` is driven.
- **The bake now runs for every candidate, and it opens no new consumer-dispatch point.** The
  arguments are the same `(negate, args, kwargs)` tuple the exact-`QuerySet` arm already baked;
  what changed is only which class may hold it. `models.Q(*args, **kwargs)` sorts `kwargs.items()`
  by unique string keys (no value comparison), and `sql.Query.add_q(rebuilt_query, ...)` is Django's
  unbound machinery over values `_deferred_value_defect` has already proven inert or
  genuine-unshadowed Django. The one slot that was still truth-tested — `negate` — is now pinned to
  an exact `bool` ahead of `~predicate if negate else predicate`, which is the single fail-open
  expression the widening would otherwise have handed to a consumer `__bool__`.
- **The bake reproduces Django's own resolution.** Django's `QuerySet.query` property bakes with
  `self._query.add_q(~Q(*args, **kwargs))` or `add_q(Q(*args, **kwargs))` and then clears the slot,
  so there is no double-bake and the package's spelling is the same predicate on a detached clone.
- **The live carry rows measure the branch they claim.** Independent spy probe
  (`docs/builder/temp-tests/050/final/test_spy_branch.py`, monkeypatching
  `types.resolvers.normalized_row_source`, which is the seam's own binding): control arm sees
  `['QuerySet', 'QuerySet']`, mounted arm sees `['_ProjectLoanQuerySet', '_ProjectLoanQuerySet']` —
  once per parent row, so the `Manager.from_queryset` mount genuinely reaches the subclass branch
  and the control genuinely does not. Without this the two arms' equal query counts would be
  consistent with a mount that changed nothing.
- **The three new live rows pass here**: `test_a_project_queryset_class_relation_costs_what_
  djangos_own_manager_costs[two-parents]`, `[three-parents]` (renamed by P2-2 to `…costs_two_prefetch_queries`, one arm), and
  `test_a_project_queryset_class_relation_answers_the_same_rows_when_awaited` — 3 passed.
- **The package tier passes**: `uv run pytest -n0 tests/utils/test_querysets.py
  tests/test_resource_policy.py --no-cov -q` → **622 passed**, no `--cov*` flag.
- **The README's new contract statements are true of the code.**
  - "a subclass of either extension — supplied as a class or as an instance — is refused at
    construction with `ConfigurationError`": `schema.py::_declared_authority` raises for both
    spellings through `_extension_entry_matches`, and it is called from
    `_consumer_extension_entries`, which runs before `super().__init__`.
  - "An exact authority instance in `extensions=` is read once as that same declaration and folded
    into the schema": `_consumer_extension_entries` drops the entry and returns its policy;
    `DjangoSchema.__init__` refuses a second declaration. `DjangoErrorPolicyExtension` defines no
    policy-carrying constructor, so "declares nothing, entry dropped" is the right reading for it.
  - "a factory that resolves to one instead refuses the operation with the stable
    `SCHEMA_CONFIGURATION_UNAVAILABLE` code": decided in `get_extensions`, code constant at
    `schema.py:375`.
  - "`DjangoSchema` gives every extension it manages — its authorities, its optimizer under a class
    entry or a factory result, the singleton-in-a-factory recipe above included, its debug
    extension — one state per operation": `_operation_states` selects by
    `issubclass(type(extension), _OperationBoundExtension)`, and exactly those four classes
    subclass it (`DjangoOptimizerExtension`, `DjangoDebugExtension`,
    `DjangoResourcePolicyExtension`, `DjangoErrorPolicyExtension`). The selection runs on the
    resolved list, so a class entry, an accepted instance and a factory's singleton all arrive.
  - Every symbol the three rewritten executable examples import resolves from the package root
    (`DjangoListField`, `DjangoOptimizerExtension`, `DjangoSchema`, `DjangoType`,
    `finalize_django_types`, `strawberry_config`, and `extensions.DjangoDebugExtension`), checked
    by importing them under the fakeshop settings.
  - `docs/README.md`'s link scaffold: 38 uses, 38 definitions, no undefined reference, no unused
    definition, every non-URL target exists on disk; the new `[django-security-policy]` sits in
    `<!-- External -->` in alphabetical position.
- **The five spec homes agree for the rows this cycle amended.** Decision 5 step 4, Decision 8,
  the Slice 3 checklist row, `## Test plan` (`### Package tier` seal-axis bullet and
  `### The raw-list row source`), and the two `## Definition of done` rows all now state the same
  three facts: the pending predicate is baked for every candidate, the malformed state is refused,
  and the evaluated source is windowed from its own rows. `## Edge cases and constraints` states no
  contradicting rule (its `OrderSet.apply_*` row already says a sealable subclass is accepted and
  normalized rather than rejected for its class); it carries no row about the carry, which is an
  absence rather than a disagreement. The same holds for Decision 15's ladder, Decision 21 and the
  authority DoD row after Cohort B's amendment on the subclass rung ("as a class or as an
  instance"). On the factory rung Decision 15 and Decision 21 say "subclasses included", but the
  DoD row says only "an entry that RESOLVES into one", which is narrower; this pass missed that.
- **Structural gates on the identified tree** (`--check` only; nothing rewritten):
  `scripts/check_trailing_commas.py --check <the 14 non-artifact paths>` → clean;
  `scripts/check_citations.py --check` → `OK: 1108 citations resolve (929 in 448 .py files, 179 in
  KANBAN.md)`; `ruff format --check` → `451 files already formatted`; `ruff check` → `All checks
  passed!`. The full gate (default suite, sharded suite, floor scope, tracked-path constants,
  `manage.py check`, `makemigrations --check`) is Worker 0's step 2 and is not restated here.

### Test staleness sweep, run independently of the diff's file list

Run over the whole tracked population (747 files) rather than the cohorts' enumerated sets, in both
polarities of the retired claim:

| Needle | Hits | Reading |
|---|---|---|
| `unresolved deferred` (tracked `.py`) | 3 | C1 above; 12 at HEAD (per-line; a line-joining reader gives 4 and 13) |
| `unresolved deferred` (tracked `.md`) | 3 | 2 archived specs + 1 quotation inside this cycle's own rationale (quoting the pre-fix message verbatim as measured evidence — correct as a quotation). Archived specs already ROUTED |
| `never copies` `_result_cache` | 4 | 3 in archived specs 035/045 (describe the VISIBILITY seal, which still does not carry — true), 1 unrelated (`docs/dry/DRY.md`) |
| `one extra query` | 3 | two describe the visibility hook's discarded cache — still true; `spec-059:563` is about fetching a deferred column |
| `no cached rows` | 0 | the retired claim is gone from every home |

Positive control: the same reader (per-line, not flattened; it missed the wrapped `permissions.py:369-370` site) finds `malformed deferred` at 4 `.py` sites, so the
instrument is not reporting zero because it is reading nothing.

### Failability audit

No new boundary enters at this review — it introduces no diff. The boundaries the assembled tree
carries are the three the cohort passes recorded (`bld-050-close-row_carry.md` `### Failability proofs`;
pass 5 recorded no new boundary): the deleted exact-`QuerySet` class gate (the widening, re-run
with the gate re-inserted — 9 rows fail across both tiers) and the `negate` exact-`bool` gate were
re-run at the recorded scopes; the `_result_cache` exact-`list` gate was accepted on Worker 2's
record and not re-run. The
mandatory re-run floor is therefore empty for this pass, and no transient source mutation was made
in this tree (`utils/querysets.py` is also named by a concurrent DRY cycle, which is a second reason
not to mutate it here).

### Hot-path budget

Present and reproducible as recorded: `bld-050-close-row_carry.md` `### Hot-path budget` (pass 2)
carries before/after wall-clock medians over 50 executions with the mounted-minus-control residual
at **+0.210 ms** after, against **+0.842 ms** before, and its instrument
(`docs/builder/temp-tests/050/row_carry/test_hotpath_admission.py`) was on disk and runnable at that pass (deleted at closeout).
The number's acceptability is the maintainer's call, not this review's.

### DRY findings

None. The diff adds one `_SealPolicy` field plus its two checks in the one sealer, one guard inside
the one bake helper, and one deleted class gate. No second rebuild primitive, no second cleanup
policy, no parallel classifier. Cross-cohort: Cohort B touches no runtime code (its `schema.py`
delta is stripped-AST identical to HEAD), so there is no convergent-shape risk between the two.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty: `__all__` and the re-export
list are unchanged, which is what the card's `## Definition of done` expects at this point —
`ListArgumentError` landed in an earlier slice and this close cycle adds no export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; the tree does not modify `CHANGELOG.md`. Also confirmed untouched:
`pyproject.toml`, `uv.lock`, `TODAY.md`, and the version literal — the Version boundary and
Decision 12 hold.

### Documentation / release sanity (historical snapshot)

- `docs/README.md`: read end to end around the three rewritten examples and the two new prose
  blocks. No plain `strawberry.Schema` schema construction survives in the file's fenced examples;
  the prose beside them was rewritten rather than left describing the old spelling (the
  "Calling `finalize_django_types()` after the `Schema(...)` construction" sentence moved onto
  `DjangoSchema`; the "before `strawberry.Schema(...)` is constructed" lead-in became "before the
  schema is constructed"). No "coming soon" / "planned" / old-version wording remains in the paragraphs the
  diff touched.
- Spec and rationale: the spec stayed at its working location (no archival in that snapshot); its
  in-flight `Status:` and the rationale's rejected alternatives were not evidence of a shipped
  card.
- KANBAN DB, `docs/GLOSSARY.md` and `docs/TREE.md` are deliberately NOT in the identified tree:
  the board move and the four generated docs are Worker 0's "Record and card" step, which is also
  the named owner of the routed glossary bodies.

### Routed and robustness items — not re-raised, each with a named owner

Re-checked on disk at this HEAD rather than carried from the artifacts:

| Item | Owner | Status |
|---|---|---|
| `docs/GLOSSARY.md` "Sealed execution queryset" body (`_result_cache` "never copied forward") | `maintainer`, Worker 0's card-close DB pass | still live, replacement absent (fixed in `f7192bfb`) |
| `docs/GLOSSARY.md` `DjangoListField` body (unqualified `LIMIT`/`OFFSET` promise) | `maintainer`, same pass | still live (fixed in `f7192bfb`) |
| `docs/GLOSSARY.md`, four `strawberry.Schema` recipe sites (Cohort B) | `maintainer`, same pass | still live (fixed in `f7192bfb`) |
| `docs/SPECS/spec-045` and `spec-034` "unresolved" → "malformed" | `maintainer` | 1 hit each |
| `docs/SPECS/spec-047` "The bound is applied by SLICING" bullet | `maintainer` | 1 hit (amended by `b3458ee8`) |
| Exact `QuerySet` carrying a foreign `_result_cache` bypasses the ceiling | `maintainer`, the DONE record's catalog (never reached `BACKLOG.md`) | pre-existing at HEAD, unchanged |
| `_UNRECOMPOSED_CHILD_POLICY` has no production reader after `fd39cac6` | `maintainer` (delete-or-correct) | unchanged (retired by `4d9f1c3d`) |
| Connection-field sidecar seam: no routing snapshot, result not re-sealed | `maintainer`, new card (spec-030 Decision 7's row) | recorded in the rationale (fixed under card 053, `fee87ac4`/`c87f4f98`) |
| **NEW — C1**, three per-line (four joined) surviving `unresolved deferred filter` sites in first-party `.py` | `maintainer`, new card or the card-close pass | recorded above with measurement (fixed in `f7192bfb`) |
| **NEW — C2/C4**, seal ordering note and the unenforced `_SealPolicy` complement sentence | `maintainer`, note only | recorded above |

### What looks solid

- The admission change is a real widening, not a relabelled detection: an input previously refused
  (`Manager.from_queryset` relation source at the raw-list seam AND at the visibility boundary) is
  now accepted and served, and the input newly refused (`negate` that is not an exact `bool`) is
  named and pinned at both tiers.
- The one truth-testing slot the widening exposed was closed in the same change rather than left
  for a later card, which is the shape Decision 20 asks for: a fail-closed typed error on state
  Django never writes, not a new admission layer.
- The evaluated-source carry is confined by construction to the one policy where nothing recomposes
  after the rebuild, and the confinement is mechanical (one policy, one call site) rather than
  documentary.
- The live proof is built so it cannot pass vacuously: two parent cardinalities, an absolute query
  count rather than an equality, separate schemas with separate optimizer singletons per arm (the pre-P2-2 setup, which P2-2 removed), and
  the async twin asserting rows rather than a count because the capture cannot see worker-thread
  work.
- The README now says three separate things where it previously fused two, and each of the three is
  checkable against a named code seam.

### Temp test verification

- `docs/builder/temp-tests/050/final/probe_message.py` — renders the `untrusted` result-seal
  message for a project `Func` subclass; the evidence under C1 conditions (b) and (c).
- `docs/builder/temp-tests/050/final/test_spy_branch.py` — the independent spy proving the mounted
  live arm reaches the subclass branch once per parent row and the control does not.
- Disposition: both are scratch, neither is promoted (the permanent oracles for the same facts are
  the two `test_resource_policy_api.py` rows and the package-tier rows this cycle added), and both
  die with the cycle (deleted at closeout). Neither writes a tracked file; the tracked `db.sqlite3` md5 is unchanged.

### Notes for Worker 1 (spec reconciliation)

No spec edit is owed by this review. The spec, its rationale and the build plan were read at this
HEAD and the amended homes agree with each other and with the code.

`Escalated:` C1 — the three per-line surviving `unresolved deferred filter` sites (four by a
line-joining reader; all fixed in `f7192bfb`). It is NOT admitted under
Decision 20 (condition (a) fails: no `## Definition of done` row states that wording), so under
Decision 22 it does not re-loop this gate and belongs on a new card rather than here. Recording it
at the close so it is not lost: two of the three are wire-reachable remediation advice naming a
cause that no longer exists, and one of them (`permissions.py:432`) contradicts a docstring this
same diff corrected 32 lines above it. Resolution paths for the maintainer: (i) fold the
three-word substitution into the card-close pass alongside the routed archived-spec fixes, which is
the same sweep and the same vocabulary; or (ii) card it with the spec-045/spec-034 rows, which are
the `.md` half of the identical population.

### Review outcome

`review-accepted` for the historical pre-candidate snapshot. No finding was admitted under
Decision 20; four candidates were recorded with their failing condition named. This does not
complete Decision 22: the candidate commit, exact-tree gate and review, and evidence-only
follow-up record are recorded at `2c66416e` / `b38184b3`.

## P2-2 disposition — public fakeshop manager declaration

The historical review's temporary manager mount is superseded. The fakeshop `Loan` model now
declares a no-op `LoanQuerySet` through `objects = LoanQuerySet.as_manager()`, which is Django's
supported project shape and retains `use_in_migrations=False`. The live resource-policy proof no
longer rewrites `Loan._meta.local_managers`, assigns manager internals, expires private caches, or
maintains a parallel control schema. It runs the existing `{ patrons { name loans { note } } }` document
against that ordinary declaration, pins an absolute two-query prefetch cost at two and three
parent cardinalities, and keeps the async payload assertion. The package-tier `_apply_rel_filters`
probe remains only as a mechanism test for the deferred-predicate rebuild; it is not used to
construct the live public project shape.

Validation for this repair: Ruff format/check, Django `check`, `makemigrations --check --dry-run`,
trailing-comma/source-layout, citations, and the spec glossary checker all pass. A direct live
probe returned the `patrons { name loans { note } }` document with status 200, no errors, and
exactly two database queries; a metadata probe confirmed the real default and reverse relation
querysets use `LoanQuerySet`, with `use_in_migrations=False` and Django's pending reverse predicate.

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
