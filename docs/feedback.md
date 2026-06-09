# Re-review — spec-030 fixes

## Round 3 — committed & re-verified (`ab17f96a`)

The fixes are now committed as `ab17f96a` ("Fix cursor stability, to-many
ordering multiplication, and totalCount scope (spec-030 review round)"). I
diffed the committed tree against the round-2 state I verified below and the
**code is byte-identical** — `ab17f96a` is exactly that work, committed, with no
new code changes. So there are **no new findings** this round; this is a
commit-state confirmation.

- **Content match** — HEAD carries the P1 fix
  (`_finalize_queryset`'s `effective = qs.query.order_by or _meta.ordering` +
  `_ends_in_unique_column`) and the P1-B fix (`_path_traverses_to_many` +
  `Min`/`Max` aggregate) verbatim. ✓
- **Suite green** — the commit message records a full run: **1427 passed / 3
  skipped / 0 failed**. That closes the round-2 certification gap (I had not run
  pytest); the maintainer did, and it is green.
- **Commit hygiene** — no `Co-Authored-By` / attribution footer (AGENTS.md
  rule 32 ✓); the message body is a precise per-finding change description.
- **Static gates re-run on HEAD** — `ruff check` clean, trailing-commas clean,
  `check_spec_glossary` OK (50/50). `__version__` still `0.0.8` (joint-cut owned).

**Still-open follow-ups (all carried from round 2, none blocking the merge):**
1. **CHANGELOG** — the OrderSet to-many change alters a **shipped `0.0.8`**
   `DjangoListField` behavior (multiplied rows → aggregate-ordered distinct
   parents), but `CHANGELOG.md` is untouched. A `### Fixed` bullet under
   `[Unreleased]` would record it. Maintainer's call (CHANGELOG-permission rule).
2. **Mixed-term GROUP BY test** — no *executing* test exercises a mixed
   scalar + to-many-aggregate `orderBy` (the `GROUP BY` functional-dependency
   edge on strict backends). Today's test asserts expression shape, not a live
   query. Forward.
3. **033 interaction note** — the to-many-aggregate `GROUP BY` will need to
   coexist with the connection-aware walker's `select_related` (WIP-033); worth
   a note in that spec so it's designed, not discovered. Forward.

Verdict: **ready.** Items 2–3 are forward-looking; item 1 is a small
documentation call. The verification report below (round 2) remains accurate for
the committed code.

---

# Re-review — spec-030 fixes applied (round 2 verification pass)

Follow-up to the original review. The maintainer applied fixes in the working
tree (uncommitted) for every finding. This pass re-reads each change **at the
source**, confirms it is correct (not merely present), checks each is pinned by a
test, and runs the `AGENTS.md` static gates.

**Certification boundary:** I verified correctness by inspection + the non-pytest
static gates (ruff, trailing-commas, glossary). Per `AGENTS.md` ("Do not run
pytest after edits; run only when explicitly asked") I did **not** run the suite,
so I certify the fixes are correct and the tests are present and correctly
targeted — not that the suite is green. Run `pytest` before committing.

**Verdict: all findings resolved correctly.** P1 and P1-B took the root-cause
fixes (not the reject-and-defer shortcuts), the spec contracts were revised rather
than dodged, and the one cross-subsystem behavior change (OrderSet to-many
ordering) was traced through every affected test. One small follow-up note on
CHANGELOG (below).

---

## Resolution summary

| Finding | Status | Fix (at source) | Pinned by |
| --- | --- | --- | --- |
| **P1** — cursors unstable over a non-unique `orderBy` / `Meta.ordering` | ✅ Resolved (root cause) | `connection.py::_finalize_queryset` now appends a terminal pk tiebreaker in **all** cases unless `_ends_in_unique_column` is already true; resolves the effective ordering as `qs.query.order_by or _meta.ordering` (the `Meta.ordering` trap I flagged) | `test_finalize_queryset_appends_pk_tiebreaker_to_non_unique_ordering`, `…skips_pk_when_terminal_already_unique`, `…preserves_meta_ordering_and_appends_pk`, `test_ends_in_unique_column_…` |
| **P1-B** — to-many ordering multiplies rows (dup nodes, skipped nodes, inflated `totalCount`) | ✅ Resolved (root cause) | `orders/sets.py::OrderSet._resolve_order_expressions` orders a to-many path by a `Min`(ASC)/`Max`(DESC) **aggregate annotation** instead of the raw fan-out path, so the parent row isn't multiplied; both `DjangoListField` and `DjangoConnectionField` benefit | `test_path_traverses_to_many_…`, `test_resolve_order_expressions_…` (×2), live `test_genre_connection_order_by_to_many_no_node_multiplication` |
| **P2** — `_total_count_requested` over-broad subtree walk | ✅ Resolved | Predicate now recurses **through** fragment wrappers only and stops at regular fields (doesn't descend into `edges`/`node`) | `test_total_count_requested_scoped_to_direct_children` |
| **P3a** — cooperation point runs without an optimizer installed | ✅ Resolved (principled choice) | `apply_connection_optimization` now short-circuits `if optimizer is None: return queryset` — no throwaway fabrication; consistent with the middleware's opt-in behavior | `test_apply_connection_optimization_short_circuits_without_optimizer` |
| **P3b** — `_connection_type_cache` not cleared by `registry.clear()` | ✅ Resolved | `connection.py::clear_connection_type_cache` wired into `registry.clear()` via a cycle-safe local import | `test_clear_connection_type_cache_…`, `test_registry_clear_also_clears_connection_type_cache` |
| **P3c** — consumer `resolver=` contract undocumented | ✅ Resolved | `DjangoConnectionField` docstring now states the `(root, info)` shape and that sidecar args are pipeline-applied, not forwarded | doc-only (no behavior) |
| **LOW** — `DjangoListField` / `many_resolver` unordered | ✅ Resolved (doc note) | `DjangoListField` docstring documents the "no order without `orderBy`/`Meta.ordering`" contract and the deliberate asymmetry with the connection | doc-only |
| **NULLS portability** | ✅ Resolved (doc note) | `orders/inputs.py::Ordering` docstring adds the SQLite-vs-Postgres NULL-placement portability note + points to the explicit `*_NULLS_*` variants | doc-only |

---

## Verified correct — the two substantive fixes

### P1 — the `Meta.ordering` trap is handled, and `_ends_in_unique_column` is sound

`_finalize_queryset` does exactly the right thing:

```python
effective = tuple(qs.query.order_by) or tuple(target_model._meta.ordering)
if not _ends_in_unique_column(effective, target_model):
    qs = qs.order_by(*effective, target_model._meta.pk.attname)
```

The `or _meta.ordering` fallback closes the trap from the previous round — a
model-default ordering lives in `_meta.ordering` while `qs.query.order_by` is
empty, so reading the latter alone would have rewritten `ORDER BY order` into
`ORDER BY pk`. `test_finalize_queryset_preserves_meta_ordering_and_appends_pk`
pins this with the kanban `Status` model (a real `Meta.ordering = ["order"]` over
a non-unique `PositiveIntegerField`) and asserts `("order", "id")` — the precise
trap, guarded.

`_ends_in_unique_column` is conservative in the right direction: it returns `True`
only for the pk or a `unique=True` model field at the terminal position; relation
paths (`shelf__code`), annotation aliases (the to-many aggregate), and
non-`F` expressions all fall through to "append pk." It tolerates both string refs
(with `-` stripped) and `OrderBy`/`F` expressions via `.expression.name`. The unit
test covers all of these shapes including the empty-ordering and aggregate-alias
cases.

### P1-B — aggregate ordering is the correct root cause, and the `totalCount` leg is now empirically confirmed

`OrderSet._resolve_order_expressions` detects a to-many path
(`_path_traverses_to_many` walks each `__` segment via `relation_kind` /
`is_many_side_relation_kind`) and emits `.annotate(<alias>=Min/Max(path))` +
`order_by(<alias>)` instead of the fan-out `order_by(path)`. The annotation forces
a GROUP BY on the parent, collapsing to one row per parent — which fixes **both**
legs I raised:

- **Cursor dup/skip** → gone: the live `test_genre_connection_order_by_to_many_no_node_multiplication`
  orders the genre connection by the reverse-M2M `books: { title: ASC }` with
  `Fiction` owning two books, and asserts `["Fiction", "History"]` with
  `len == len(set(...))` — no duplicate node.
- **`totalCount` inflation** → my earlier "Likely, pending empirical check" is now
  **confirmed fixed**: the same live test asserts `totalCount == 2` (distinct
  genres, not the multiplied genre×book rows). The GROUP BY makes `.count()` count
  groups = distinct parents. This is exactly the uncertainty I couldn't resolve
  without running code; the live test resolves it.

The fix lives in `OrderSet` (not bolted onto the connection), so `DjangoListField`
is corrected too — the right layering.

**Spec contract revised, not dodged.** `spec-028` Slice-4 prose is marked
**superseded**: the old "Branch appears N times" raw-multiplicity contract is
replaced with the aggregate (Alpha then Beta, each once), citing P1-B. `spec-030`
Decision 7 / Goal 3 / the pipeline pseudo-code / the Edge-cases section are all
updated to the terminal-pk-tiebreaker semantics with the `Meta.ordering` trap
documented and the non-unique-vs-concurrent distinction made explicit.

**No missed regression from the behavior change.** I checked every other to-many
order test. `test_library_branches_order_by_reverse_fk_relation` was updated
(`[Alpha, Beta, Alpha, Alpha]` → `[Alpha, Beta]`). The M2M test
`test_library_books_order_by_m2m_absolute_import_path` was **not** changed and does
**not** need to be: it seeds exactly one genre per book, so there is no
multiplicity — raw-JOIN and aggregate produce the identical 3-distinct-row result.
The permission tests that order by `shelves` assert a denial (error), not row
shape, so they're unaffected.

---

## AGENTS.md re-check

- The previously-flagged ⚠️ row ("root-cause over surface patch") is now ✅: P1
  and P1-B both took the root-cause fix. Notably, the reject-in-connection /
  reject-now-plus-card options were **not** taken — which is the correct reading
  of `AGENTS.md` line 4 ("never propose ship-it-today-defer-the-real-fix
  sequencing … pragmatic shortcuts are NEVER a viable answer … even with a
  follow-up card").
- Static gates: `ruff check` clean on all six changed source files;
  `check_trailing_commas.py --check` clean; `check_spec_glossary.py` OK (50 terms,
  all resolve). `__version__` still `0.0.8` (joint-cut owned) — untouched.

**One follow-up (small, maintainer's call):** the OrderSet to-many change is a
user-observable behavior change to a **shipped `0.0.8`** feature (`DjangoListField`
ordering by a to-many relation now returns distinct, aggregate-ordered parents
instead of multiplied rows), but `CHANGELOG.md` was not touched. A `### Fixed`
bullet under `[Unreleased]` would record it. This arguably falls inside the
spec-030 cut's CHANGELOG-edit grant (same `0.0.9` line), but since that grant is
scoped to the connection-field surface it's worth an explicit decision rather than
an assumption — consistent with the "don't infer CHANGELOG permission" rule.

---

## Residual / forward-looking notes (not blockers)

- **GROUP BY functional-dependency on strict backends.** A mixed `orderBy`
  (scalar term + to-many aggregate term) produces
  `.annotate(Min(rel)).order_by(scalar_col, alias)`, which groups by the parent pk
  and orders by a non-pk scalar column. Postgres (≥9.1) and MySQL (5.7+ with
  `ONLY_FULL_GROUP_BY`) both resolve that scalar as functionally dependent on the
  pk, and SQLite is lax — so this is correct on the tested + common backends, but
  worth a glance on the production DB. Not exercised by a mixed-term test today
  (the unit test covers `[to-many, scalar]` shape-wise but doesn't execute it);
  an executing live test would close that.
- **033 interaction.** When the connection-aware walker (WIP-033) makes the
  optimizer plan non-empty, its `select_related` columns will need to coexist with
  the to-many-aggregate GROUP BY. Worth a note in the 033 spec so the interaction
  is designed, not discovered.

---

## Still-good (carried over, re-confirmed)

The source-verified mechanism, the `graphql_type_name` collision fix, the
await-before-raise async discipline with its GC regression test, the M1
non-queryset guards, the shared `_validate_djangotype_target` / `apply_to`
extractions, and `_is_relay_shaped` single-sourcing all remain intact and were not
disturbed by the fixes.
