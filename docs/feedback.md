# spec-034 Permissions — Fix Verification (final pass)

Re-checked the spec against the seven updates the deep architectural evaluation
proposed, using the same code references I confirmed while placing the
`TODO(spec-034 Slice N)` anchors. Verdict: **all seven applied and correct — the
spec is ready to build.** One technical dispute adjudicated in the spec author's
favor (verified against Django source), and two minor revision-ledger
inconsistencies left to tidy.

## Each proposed update — verified applied

1. **Decision 12 — Prefetch-path `info` threading (the load-bearing one).** ✓
   Applied. The decision now carries a "Verified dependency to protect" paragraph
   citing `optimizer/walker.py::_build_child_queryset` (walker.py:212-214) — the
   `apply_type_visibility_sync(target_type, queryset, info)` call that threads the
   live `info` into the nested hook — and states the consequence (a refactor that
   drops `info` silently breaks transitivity), plus a Slice-2 pin that the nested
   cascade narrows *with the request user*, not just that a `Prefetch` is planned.
   This is exactly the protection I wanted and it matches the code.

2. **Edge cases (4 bullets).** ✓ All four applied:
   - **MTI parent-link** — excluded by design (`not getattr(field.remote_field,
     "parent_link", False)`), with the "child hidden when MTI parent hidden is a
     surprising security inclusion" rationale and a synthetic-graph pin (no
     fakeshop MTI). Correct.
   - **Cascade-target return contract** — added, and *better than I framed it*: it
     correctly distinguishes the slice behavior per backend (see the adjudication
     below) and covers `.values()` (wrong column / `ValueError`) and
     `.distinct("field")` (Postgres subquery error). Documented as a GLOSSARY
     (Slice 5) contract item.
   - **`fields=[]`** — defined as an explicit no-op, distinct from `None`, with the
     reasoning for *not* raising (a well-formed empty iterable is unambiguous;
     supports programmatically-built edge sets).
   - **Secondary-as-root** — added: a model's transitive visibility is always its
     *primary* type's hook regardless of which type rooted the call; terminates
     because `secondary ≠ primary` in the seen-set. Pinned + documented.

3. **Decision 8 / "Sharded callers" — claim narrowed.** ✓ Applied. Now states
   alias propagation is "per-handed-queryset, not global": the direct call inherits
   `queryset.db`, but the prefetch-composed cascade follows the prefetch child's
   per-model routing (`_build_child_queryset`, walker.py:212). Matches the code.

4. **Decision 9 — per-call validation redundancy.** ✓ Applied. One sentence now
   acknowledges the `fields=` check is technically redundant per request (a
   compile-time-constant arg against a post-finalize-stable set), bounded, and
   absorbed by the recorded memo fallback — "a known, measured cost rather than an
   oversight."

5. **Slice 1 test plan — multi-DB harness named.** ✓ Applied. The
   `test_multi_db_subquery_pinned_to_caller_alias` pin now carries a "Harness note":
   default settings define only `"default"`; `shard_b` is `FAKESHOP_SHARDED`-gated
   (`examples/fakeshop/config/settings.py` ~line 116); build on the established
   `tests/optimizer/test_multi_db.py` pattern "rather than reinventing one or
   quietly skipping the pin." This was the gap most likely to silently drop a
   security pin — now closed.

6. **Slice 4 — seeder audit promoted to a checklist item.** ✓ Applied. The
   `is_private`-defaults audit + suite re-pin is now a bold Slice-4 checklist line
   ("the single most likely source of churn ... a load-bearing setup step, not a
   contingency"), not a Risks fallback.

7. **H1 — absolute upstream path.** ✓ Fixed (better than expected). The
   `[upstream-permissions]` link is now
   `https://github.com/riodw/django-graphene-filters/blob/master/...`, and `grep`
   finds **no** remaining `/Users/...` absolute path anywhere in the spec.

## Technical adjudication — the slice rebuttal is correct

The spec author *declined* the original "sliced target queryset raises
`NotSupportedError`" finding (Revision 4), arguing it is backwards:
`allow_sliced_subqueries_with_in` defaults `True`, so SQLite/PostgreSQL compile
`IN (SELECT … LIMIT n)` fine and only MySQL raises. **Verified against Django
source** — `django/db/backends/base/features.py:49` sets it `True`;
`django/db/backends/mysql/features.py:11` is the only override to `False`. The
rebuttal is right: there is no universal raise. And the spec did the honest thing —
rather than simply dropping the concern, it folded the *accurate* version into the
cascade-target-contract bullet (MySQL hard-errors; SQLite/PostgreSQL silently
mis-narrow), which is the real, backend-aware risk worth documenting. Good call;
my original generalization over-claimed the raise.

## Two minor revision-ledger inconsistencies (LOW — tidy when convenient)

Not blockers; both are about the spec's own change-log accuracy, not its design:

- **The Revision 4 note is now stale on H1.** It says the hardcoded path was "left
  unchanged pending a maintainer decision," but the link *was* repointed to the
  GitHub URL (confirmed above). Update the note to record the fix, or it reads as
  contradicting the shipped link.
- **No revision entry records the deep-architectural-eval pass.** The revision
  history runs to Revision 4 (asgiref/slice/path), but the largest edit set — the
  MTI exclusion, secondary-as-root, Decision 8 narrowing, Decision 9 redundancy,
  the Decision 12 verified-dependency paragraph, the multi-DB harness note, and the
  Slice-4 checklist promotion — has no Revision 5 entry. Add one so the ledger
  reflects what changed (the spec's own convention is to record each review pass).

## Cross-checks (all green)

- `scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` →
  `OK: 43 terms`.
- `permissions.py` still imports clean and `tests/test_permissions.py` collects
  (26 skipped stubs) — the staged seams are intact under the spec edits.

## Net

The architecture was sound before; it is unchanged. Every actionable finding from
the deep evaluation is now in the spec (correctly, including a sharper version of
the slice nuance than I proposed). The only residue is two one-line revision-note
tidies. **Ready to write production code, starting with Slice 1.**
