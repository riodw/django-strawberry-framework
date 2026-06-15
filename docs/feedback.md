# spec-034 Permissions — Deep Architectural Evaluation

A pre-production architectural pass over `docs/spec-034-permissions-0_0_10.md`,
done after laying the `TODO(spec-034 Slice N)` anchors across the codebase. Every
claim below was checked against the live code, not the prose.

## Executive verdict

**Architecturally sound; no redesign needed.** The core mechanism (call-time
single-column-forward walk, `ContextVar` cycle guard, lazy `__in` subquery
composition, registry-primary targeting, `has_custom_get_queryset()` gate) is
correct, and the one load-bearing assumption that worried me — "every nested
relation respects the cascade *for free* via the Prefetch downgrade" — is
**verified true** in code. The findings are edge-case/contract clarifications and
two test-setup callouts, all fixable with small spec edits before we write
production code.

One framing correction up front, because it changes the answer to question 3:
**this card introduces no setting.** The "setting read/validation anchor in
`types/relay.py`" the prompt asks about does not exist for spec-034 (details in §3).

---

## 1. Inconsistencies & contradictions

**Verified sound (the assumption I most wanted to break):** Decision 12 / Goal 3
claim a cascading hook composes transitively through the optimizer's
`select_related → Prefetch` downgrade with no new code. This only works if the
optimizer calls the target's `get_queryset` **with the live request `info`** when
it builds the prefetch child (otherwise the cascade, which reads
`info.context.user`, has no user and either errors or silently no-ops). It does:
`optimizer/walker.py::_build_prefetch_child_queryset` (walker.py:212-215) builds
`field.related_model._default_manager.all()` and, when
`_target_has_custom_get_queryset(...)` is true, runs it through
`apply_type_visibility_sync(target_type, queryset, info)` — the same live `info`
threaded from the root walk. So the cascade runs inside the prefetch child with
the request user. Decision 12 is not hand-waving; it holds. Worth stating in the
spec as a *verified* dependency (with the walker.py:214 cite) so a future
optimizer refactor that drops `info` from that call knows it would silently break
cascade transitivity.

**Ambiguity (LOW) — secondary-type root vs. primary transitive target.** The walk
resolves every target with `registry.get(model)` → the **primary** type (Decision
5 step 2), and Edge cases pins "secondaries are never cascade *targets*." But a
consumer can legally declare `get_queryset` (and call the cascade) on a
*secondary* type, making it the **root**. When the transitive walk re-reaches that
secondary's model through another edge, it narrows with the **primary's** hook,
not the rooting secondary's. The cycle guard keys on the class object, so
`secondary ≠ primary` in the seen-set — terminating correctly (the primary lands
in the set on its own visit), but the row visibility of that model depends on
which type rooted the call. This is probably the intended "secondaries don't
auto-resolve" semantics, but the spec never states the root-secondary case.
Recommend a one-line Edge-cases bullet.

**No contradiction with existing patterns.** The `a`-prefix naming (Decision 4),
the `SyncMisuseError` reuse from `utils/querysets.py` (Decision 10), the
`has_custom_get_queryset()` gate (Decision 5), and the "cascade narrows first,
gates judge input second" order (Decision 11) all match shipped conventions I
re-verified while anchoring.

## 2. Missing edge cases

**MTI parent-link edges cascade silently (MED).** The scope test (Decision 5 step
1: `related_model` present AND `hasattr(field, "column")`) is meant to select
single-column forward FK/O2O and exclude M2M/reverse/generic/composite. But a
**multi-table-inheritance** child model carries an auto-generated
`<parent>_ptr` `OneToOneField(parent_link=True)` that **has a `column`** — so it
passes the test and the cascade will walk it and narrow a child row by its MTI
parent type's hook. The spec enumerates every *exclusion* but never addresses this
*inclusion*. Is "a child row is hidden when its MTI parent is hidden" intended? It
may be defensible, but it's unstated, and no fakeshop model uses MTI (`grep`
confirms none), so it would ship completely untested. Recommend an explicit
decision: either document MTI-parent-link cascade as intended, or exclude it with
`not getattr(field.remote_field, "parent_link", False)`.

**Target `get_queryset` must return a plain row queryset (MED) — generalize the
slice finding.** The prior review's M1 correctly flagged that a target hook
returning a *sliced* queryset (`queryset[:10]`) makes `Q(fk__in=target_qs)` raise
`NotSupportedError` (LIMIT inside `IN`). The same break occurs for a hook
returning `.values()`/`.values_list()` (wrong/missing pk column for the `__in`)
or `.distinct("field")` (Postgres field-distinct in a subquery). This is one
class — *the cascade-target contract* — not just slicing. Recommend a single
Edge-cases bullet: "a cascade-target's `get_queryset` must return an unsliced,
non-`.values()` model-row queryset; the cascade composes it as an `__in`
subquery." This is also a doc/contract item for the GLOSSARY body (Slice 5).

**`fields=[]` is a silent no-op (LOW).** Decision 9 handles the bare-string guard
and unknown/non-cascadable names, but an explicit empty list validates clean
(`set([]) - cascadable == ∅`) and then the walk skips every edge — cascading
nothing. That is almost certainly a consumer mistake (they meant `fields=None`).
Given the spec's own "loud on ambiguity" posture (the bare-string guard precedent),
recommend either documenting `fields=[]` = "cascade nothing" intentionally or
treating it as suspect. Low severity, one line.

## 3. Configuration & performance risks

**The premise does not apply to this card — there is no setting.** Spec-034's
Non-goals are explicit: *"No `DJANGO_STRAWBERRY_FRAMEWORK` entry is needed; the
cascade is configured at the call site"* (spec line 117). There is **no**
setting read and **no** setting-validation anchor in `types/relay.py` for this
card. The setting read in `types/relay.py` (lines 359-398) is
`RELAY_GLOBALID_STRATEGY` — that belongs to **spec-031** (GlobalID encoding) and
is unrelated to the cascade. So the lazy-config-evaluation / config-thread-safety
/ redundant-config-validation concerns the prompt raises have no surface to land
on here. (If the concern is carried over from the spec-033 review — that card *did*
read `relay_max_results` from the schema config — it does not transfer to 034.)

The runtime surface this card *does* introduce, and how it nets out:

- **Per-call model-graph walk** — the walk runs on every `get_queryset`
  invocation (per request on root fields, per prefetch-child build on downgraded
  relations). It is one `model._meta.get_fields()` loop plus set operations — no
  I/O, no lock. The spec already flags this (Risks: "Cascade-call overhead on hot
  paths") with the right fallback: a per-`(model, fields)` memo of the edge list
  (not the querysets) behind the same public surface. Correctly deferred under
  measure-first.
- **Per-call `fields=` validation (minor redundancy).** Decision 9's set
  comparison runs every call, yet `fields=` at a call site is a compile-time
  constant — the cascadable set is stable post-finalize, so the validation result
  never changes across requests. It's genuinely negligible (a small set diff), but
  it *is* redundant per-request work; the same memo fallback would absorb it.
  Worth one explicit sentence in Decision 9 so it's a known, bounded cost rather
  than an oversight.
- **Thread-safety: sound, no issue.** The `ContextVar` (not a module global) is
  the correct primitive, and Decision 10 (Revision note) already records that the
  `sync_to_async(thread_sensitive=True)` async variant is safe because asgiref
  copies the context into the worker thread (`copy_context()` semantics) — the
  walk sees a clean seen-set and contains its mutations to the copy. I re-checked
  the reasoning; it's correct. No shared mutable state crosses requests or threads.

**One genuine multi-DB nuance (LOW-MED) the spec overstates.** Decision 8 / Edge
cases ("Sharded callers") claim a caller's `.using("shard_b")` "propagates into
*every* cascade subquery." True for the **direct call** (`.using(queryset.db)`
reads the caller's resolved alias). But when the cascade runs inside an
**optimizer-built prefetch child**, the base is
`field.related_model._default_manager.all()` (walker.py:212) whose `.db` is the
*router-resolved* alias for that model — not the root request's explicit
`.using("shard_b")`. So in the prefetch path the cascade pins to the prefetch
child's own routed alias, not the root's. This is likely *correct* (each model
routes itself), but it contradicts the "every subquery inherits the caller's
alias" wording. Recommend narrowing the claim: alias propagation holds for the
direct call; the prefetch-composed cascade follows the prefetch child's
per-model routing.

## 4. Test & documentation gaps

**The synthetic-graph infrastructure already exists — no major rewrite.** The four
invariant pins need synthetic model graphs (cycles A↔B, self-FK, async hooks) the
fakeshop schema lacks, but the package suite already builds `managed=False`
synthetic models with relations under registry isolation (the override-fixture
pattern), and `pytest-asyncio` is configured (`mode=Mode.AUTO`) for the async
pins. So Slices 1-3 fit the existing harness.

**Multi-DB invariant pin needs a second alias — name the harness (MED).**
`test_multi_db_subquery_pinned_to_caller_alias` requires a second DB alias to
prove `.using("other")` pinning. The default package settings define only
`"default"`; `shard_b` is **`FAKESHOP_SHARDED`-gated** (`examples/fakeshop/config/
settings.py:117`), so a default `uv run pytest` has one DB. There *is* precedent —
`tests/optimizer/test_multi_db.py` — so this is not a rewrite, but the spec's
Slice-1 test plan should name that harness (the `FAKESHOP_SHARDED` gate or the
in-test alias pattern `test_multi_db.py` uses) so the builder doesn't reinvent it
or quietly skip the pin. As written, the pin reads as runnable in the default
suite, and it isn't.

**Slice 4's biggest risk is a checklist item, not a fallback (MED).** Activating
the four products `get_queryset` hooks flips anonymous-request visibility across
the **entire** products live suite, not just the new tests. The spec records this
under Risks ("Live-suite sensitivity") with a fallback, but the concrete,
load-bearing setup step — *audit the products seeders' `is_private` defaults and
re-pin every existing assertion that counted would-be-hidden rows* — should be a
Slice-4 **checklist line**, not a contingency. It is the single most likely source
of churn when the card lands.

**Doc gap (carried, still open): H1 absolute path.** The `[upstream-permissions]`
link still points at a hardcoded local absolute path
(`/Users/riordenweber/projects/django-graphene-filters/...`, spec lines ~79/632) —
unresolvable for anyone else / CI / GitHub. Replace with the upstream repo URL or
a non-path reference. (Logged in the prior review; not yet applied.)

---

## Proposed spec updates (minimal, no redesign)

1. **Decision 12** — add the verified `optimizer/walker.py:214` cite as the
   mechanism that makes prefetch-path transitivity work, framed as a dependency to
   protect.
2. **Edge cases** — add bullets for: (a) MTI `<parent>_ptr` edges (decide
   intended-or-excluded); (b) the cascade-target `get_queryset` contract (unsliced,
   non-`.values()` row queryset — generalizes the slice finding); (c) `fields=[]`
   semantics; (d) secondary-as-root + primary-as-transitive-target narrowing.
3. **Decision 8 / "Sharded callers"** — narrow the "every subquery" claim: direct
   call inherits the caller alias; the prefetch-composed cascade follows per-model
   routing.
4. **Decision 9** — one sentence acknowledging the per-call `fields=` validation
   is redundant-but-bounded, absorbed by the recorded memo fallback if it ever
   matters.
5. **Test plan (Slice 1)** — name the multi-DB harness for the alias pin
   (`FAKESHOP_SHARDED` / `tests/optimizer/test_multi_db.py` pattern).
6. **Slice 4 checklist** — promote the seeder `is_private` audit + suite re-pin
   from a Risks fallback to an explicit checklist item.
7. **Links** — fix the absolute `[upstream-permissions]` path (H1).

None of these touch the architecture. Once folded in, the spec is ready to build.
