# Rationale: spec-023 — Multi-database cooperation contract (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-023-multi_db-0_0_7.md`][spec-023]. The spec is the contract and states only what it requires; everything that explains **how it got there** lives here: the five-revision inline changelog the spec carried, the justification and rejected alternatives behind each of the nine Decisions, and every claim a Decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, run late — as a residual-completion cycle rather than at the card's own pre-flight, because the original `023` cycle never performed step 7. It was produced by Slice 1 of `docs/builder/build-023-multi_db-0_0_7.md`. Slice 2 of that plan reconciled the spec against `HEAD` and appended its own record below, under `## Slice 2 — spec reconciliation`; every forward pointer in the Slice 1 text is closed there.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** Every block quoted below under a `### Justification (moved from the spec)` or `### Alternatives considered (and rejected)` heading, and the whole of `## Revision history`, was cut from the spec by this pass; none was written from memory. The per-Decision `### Changes this Decision underwent` records are the exception and are new material — the original cycle never wrote a change record because it never ran this pass.

What the spec carried immediately before the cut, measured at this working tree:

| Population | Measured | Instrument |
|---|---|---|
| `Revision history` entries, inline | 5 | `grep -cE '^\- \*\*Revision [0-9]+\*\*'` |
| numbered findings inside those entries | 37 | `grep -c '^  [0-9]*\. \*\*'` |
| `Justification:` blocks at line start | 9 | `grep -c '^Justification:'` |
| `Justification`-prefixed clauses **anywhere** | 11 | `grep -oE 'Justification[a-z ]*:' \| wc -l` |
| `Alternatives considered (and rejected):` lists | 7 | `grep -oE 'Alternatives considered' \| wc -l` |
| `(revN Xn)` attribution parentheticals | 130 | `grep -oE '[Rr]ev[0-9]+(-post)? [A-Z][0-9]+' \| wc -l` |
| bare `rev[0-9]` token occurrences | 202 | `grep -oE 'rev[0-9]' \| wc -l` |

**The 9-vs-11 gap matters the same way it did on `spec-022`.** Two `Justification:` clauses sit mid-bullet where a line-anchored grep cannot see them: one in the `## Slice checklist` Slice 3 "No edits to `README.md` / `GOAL.md` / `TODAY.md`" bullet, one in `## Doc updates`' "No edits to `docs/TREE.md`" bullet. Both are one-clause scope statements rather than deliberation blocks, and both **stay** in the spec — they are the reason a doc is *not* edited, which is contract. The count is recorded so the next reader does not mistake 9 for the population.

**The 130-vs-202 gap is not a discrepancy either.** `130` counts attribution parentheticals of the `revN Xn` shape; `202` counts every `rev[0-9]` token, which additionally includes prose mentions ("rev1's broader claim", "post-rev3-R2", "the rev2-narrowed contract") that carry no finding id. After this pass, `grep -cE 'rev[0-9]'` against the spec returns **0**.

**Measured byte counts, `wc -c` at this working tree:**

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-023-multi_db-0_0_7.md` | 163,336 | 110,831 |
| `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` | 0 (did not exist) | 84,471 |

The **Before** figure is the on-disk size when this pass opened the file, not the size at `HEAD`. The spec was already dirty: `git show HEAD:docs/SPECS/spec-023-multi_db-0_0_7.md | wc -c` reports **163,533**, and a concurrent session rewrote nine stale reference ids (`spec-016` -> `spec-020`, `spec-017` -> `spec-021`, `spec-018` -> `spec-022`, `spec-019` -> `spec-023`, and their `-terms` / `Decision 10` companions) plus four `AGENTS.md` quote substrings at 19:46 while this pass was reading. That edit is another session's work and was left untouched (`AGENTS.md` rule 34); this pass measured, cut, and re-measured against the post-19:46 content.

The byte figures above were produced by writing this table with fixed-width placeholders, running `wc -c` on both files, then substituting equal-width digits, so the substitution cannot move the number it reports.

`HEAD` at the time of the pass is `31625ac7`. The package is at `0.0.14`; this card shipped at `0.0.7` on 2026-05-27 as `DONE-023-0.0.7`.

**Moved** — cut from the spec by this pass, and now only here:

- the whole `Revision history (kept inline so the spec is self-contained)` block: all five revisions, 37 numbered findings (rev2 H1-H10 / S11-S13, rev3 R1-R10, rev4 V1-V8, rev5 X1-X6);
- all nine line-start `Justification:` blocks except [Decision 6][spec-023-d6]'s, which stays in the spec (see below);
- the `Alternatives considered (and rejected):` list under Decisions 1, 2, 4, 5, 6, 7, and 9 — seven lists in total; Decisions 3 and 8 never carried one;
- every `revN Xn` attribution parenthetical threaded through `## Key glossary references`, `## Slice checklist`, `## Goals`, `## Current state`, `## Problem statement`, `## User-facing API`, `## Implementation plan`, `## Edge cases and constraints`, `## Test plan`, `## Doc updates`, `## Risks and open questions`, `## Out of scope`, and `## Definition of done` — the change each one records is now in this file under the Decision it touched.

**Stayed in the spec** — deliberation-shaped text the [`worker-1.md`][worker-1] implementation-relevant carve-out keeps:

- **[Decision 6][spec-023-d6]'s whole `Justification:` block.** Its three bullets are the mechanism that makes `pytest.skip(..., allow_module_level=True)` correct and `pytest.mark.skipif` wrong: `config.settings` decides `DATABASES` at module-import time, so a mark evaluated after import cannot prevent the model imports from running against a single-DB `DATABASES` dict. A builder who never reads that writes the `skipif` form and the module fails to import in single-DB mode. This is the one place the move could itself have caused a defect.
- **The pinned-header annotations under [Decision 6][spec-023-d6]** explaining why `importlib` / `sys` are imported and why `DjangoType` / `finalize_django_types` are NOT. Both exist to stop the next editor "fixing" an import list; removing them re-opens an `F401`-versus-`# noqa` trap the Slice 2 checklist forbids.
- **The `## Risks and open questions` section in full.** Each bullet is a preferred answer for `0.0.7` plus a fallback if implementation proves it wrong — forward-looking contingency, not chronology. Only the `revN Xn` attributions inside it were cut.
- **Every "verified against `<source>`" clause** whose object is a live mechanism (`_build_child_queryset` starting from `_default_manager.all()`, the `plan_optimizations` signature, the `per-file-ignores` entry). The attribution was cut; the verification stayed.
- **The `## Test plan` FieldMeta-construction and synthetic-`selected_fields` pins**, reworded from "so Worker 2 doesn't have to …" to role-neutral phrasing. They tell an implementer what shape to build; that is instruction.

**Deleted, not moved** — prose whose only reason to exist was to correct an earlier revision, per [`worker-1.md`][worker-1] `### Performing the rationale move` rule 2:

1. `## Edge cases and constraints`: "The missing-docstring code for free test functions would be `D103` (function-level), not `D102` (class-method-specific) either way." A true sentence about a claim (`D102` is required) that no longer appears anywhere; it documented a deleted error.
2. `## Edge cases and constraints`: "Rev1's wording of 'run a queryset through `plan_optimizations`' referred to an API that does not exist; rev3's wording of `plan_optimizations(selections, model, parent_type)` mis-positioned the third argument." Pure chronology of two superseded wordings; the corrected call shape is stated directly two sentences earlier.
3. `## Slice checklist`: "mirroring [`spec-021`] rev4 informational item 2 and [`spec-022`] rev2 M1" — a cross-spec citation into two sibling specs' revision numbering, which those specs' own rationale moves have since retired. The rule it cites (one pytest item per test, no `parametrize`) is stated in the same sentence and survives.
4. The rev5 X1 / X2 / X3 letter-correction narratives in [Decision 3][spec-023-d3], `## Edge cases and constraints`, and `## Risks and open questions`. The corrections themselves are recorded under [Decision 3](#decision-3--the-cooperation-contract-four-axes) below; the narrative of which letter was wrong in which revision is not something the spec may narrate. **One of these letter drifts survived every revision and is still live in the spec** — see `## Claims the spec may no longer make` item 4.
5. Four now-orphaned link definitions (`[spec-018]`, `[spec-019]`, `[spec-021]`, `[next-step-8--archive-prior-specs-and-update-cross-references]`) whose only uses left with [Decision 1][spec-023-d1]'s justification and the Slice-checklist clause above. Their targets are cited in this file instead.

**Anchor keying.** Every Decision heading below reproduces the spec's heading text, so this file's own anchors mirror the spec's. The spec links back with `[rationale-d1]` … `[rationale-d9]`, defined in its link block.

## Revision history

Five revisions of pre-ship review, kept verbatim as the spec carried them. Every in-page anchor in the original text now resolves as a cross-file link into the spec.

- **Revision 1** — initial draft. Pins the canonical spec filename (`docs/spec-023-multi_db-0_0_7.md`, NOT the [`KANBAN.md`][kanban] card body's ad-hoc `docs/spec-multi_db.md` — pinned in [Decision 1][spec-023-d1]), the no-production-code-change scope (the cooperation already exists in [`django_strawberry_framework/types/resolvers.py`][resolvers] at `django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"state.db = router.db_for_read"` — `state.db = router.db_for_read(field_meta.related_model, instance=instance)`; this card's job is to spec + test + document that cooperation, pinned in [Decision 2][spec-023-d2]), the four-axis cooperation contract (database routers via `router.db_for_read`, explicit `.using(alias)` querysets, `_state.db` propagation through FK-id elision stubs, optimizer plan / strictness / `get_queryset` downgrade routing — pinned in [Decision 3][spec-023-d3]), the test layout (`tests/optimizer/test_multi_db.py` with mocked router for hermetic package-internal coverage per [Decision 5][spec-023-d5]; fakeshop live-HTTP coverage under `examples/fakeshop/test_query/` per [Decision 6][spec-023-d6] gated on `FAKESHOP_SHARDED=1` via `pytest.skip(...)` rather than `pytest.mark.skipif` because the env var changes `config.settings.DATABASES` at module-import time), the GLOSSARY entry flip from `planned for 0.0.7` to `shipped (0.0.7)` in Slice 3, the `docs/README.md` `### Sharded mode (multi-DB)` one-line forward-pointer per the card DoD, the joint-`0.0.7` cut policy ([Decision 9][spec-023-d9]), and zero new public exports. Out of scope: first-class sharding-aware planning (cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`) — [`BACKLOG.md`][backlog] item 41 owns that.
- **Revision 2** (post-rev1 review) — six high-priority contract corrections (H1–H6), four high-priority fakeshop live-test corrections (H7–H10), and three spec-hygiene corrections (S11–S13); all surfaced by the rev1 reviewer:
  1. **H1**: rev1's [User-facing API][spec-023-user-facing-api] "Default usage — `DATABASE_ROUTERS` and implicit `db_for_read`" section claimed "the `_db` attribute is set on the queryset before the optimizer's plan application." Verified false against Django's queryset semantics: implicit-router querysets keep `_db is None` until evaluation, when Django consults `queryset.db` / the router. Fix: rewrite the implicit-router section to clarify three distinct cases — explicit `.using(alias)`: package preserves `_db` through `only()` / `select_related()` / `prefetch_related()` (axis 2); implicit router: package leaves `_db` unset, lets Django route at evaluation time; FK-id elision stubs: explicit `router.db_for_read(related_model, instance=parent_or_none)` because freshly-built model instances don't inherit a queryset alias (axis 1).
  2. **H2**: rev1's [Test plan][spec-023-test-plan] test (f) `test_get_queryset_downgrade_preserves_using_alias_on_prefetch` asserted `Prefetch.queryset._db == "shard_b"` against a parent `Model.objects.using("shard_b")` queryset. Verified false against [`optimizer/walker.py::_build_child_queryset`][walker]: it constructs child querysets from `field.related_model._default_manager.all()` then optionally applies `target_type.get_queryset(queryset, info)` — the parent queryset's `_db` is NOT threaded through. Fix: narrow [Decision 3][spec-023-d3] axis 3 to "consumer-provided `Prefetch(queryset=...)` keeps its own `_db`; generated `Prefetch` querysets do not promise `_db == parent._db` at plan-construction time — Django's router / instance hints own that path at evaluation"; rewrite the test as a consumer-provided-`Prefetch` round-trip via [`OptimizerHint.prefetch(Prefetch(...))`][glossary-optimizerhint] instead. Production-code expansion (threading parent `_db` into generated child querysets) is deliberately deferred per [Decision 2][spec-023-d2].
  3. **H3**: rev1's [Test plan][spec-023-test-plan] test (d) `test_optimizer_plan_preserves_queryset_using_alias` said "run a GraphQL selection through `walker.plan_optimizations` against a queryset constructed via `Model.objects.using('shard_b').all()`." Verified against [`optimizer/walker.py::plan_optimizations`][walker]: `plan_optimizations(...)` accepts selections + model + parent_type, NOT a queryset; the parent queryset is applied via [`OptimizationPlan.apply(queryset)`][plans] at [`plans.py::OptimizationPlan.apply`][plans]. Fix: rewrite the test to (a) build a plan with `plan_optimizations(...)`, (b) call `plan.apply(qs)` where `qs = Model.objects.using('shard_b').all()`, (c) assert `result._db == 'shard_b'`. The `OptimizationPlan.apply` path is the right unit of contract; the `plan_optimizations` call has no queryset to consult.
  4. **H4**: rev1's [Test plan][spec-023-test-plan] lumped `_build_fk_id_stub(...)` and `_check_n1(...)` tests under `tests/optimizer/test_multi_db.py`, but both functions live in [`django_strawberry_framework/types/resolvers.py`][resolvers]. Per [`docs/TREE.md`][tree]'s mirror rule (source subpackage `X/Y/` ↔ test subpackage `tests/Y/`), resolver-level unit tests belong in `tests/types/test_resolvers.py`. The [`KANBAN.md`][kanban] card body names `tests/optimizer/test_multi_db.py` as a single file, but that names the optimizer-level surface; resolver-level tests are an additive companion. Fix: split into two new test files per [Decision 5][spec-023-d5] — resolver-level tests (FK-id elision router call + the null-FK / no-`_state` branches) extend `tests/types/test_resolvers.py`; optimizer-level tests (`OptimizationPlan.apply` preserves `_db`; consumer-provided `Prefetch(queryset=...)` round-trip) land in new `tests/optimizer/test_multi_db.py`. Honors the mirror rule and the card's named file; the split is stated explicitly so future maintainers don't reverse it.
  5. **H5**: rev1's [Slice checklist][spec-023-slice-checklist] and [Goals][spec-023-goals] item 2 (c) conflated two separate `_build_fk_id_stub` branches into one test: "the FK-id elision stub returns `None` for a `None` FK (the `instance` arg is forwarded as `None` when the parent row has no `_state` attribute)." Verified against [`types/resolvers.py::_build_fk_id_stub`][resolvers]: null FK takes the early `return None` branch BEFORE `router.db_for_read` is called; parent-lacks-`_state` is a different code path that DOES call the router with `instance=None`. Fix: split into two tests — `test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router` (covers the early return; asserts the router was NOT called) and `test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state` (covers the `instance=None` forwarding; asserts the router WAS called with `instance=None`).
  6. **H6**: rev1 said strictness mode "tracks the originating connection" and the [Test plan][spec-023-test-plan] test (e) `test_strictness_mode_lazy_load_fires_under_using` claimed it fires "on the queryset's connection." Verified false against [`types/resolvers.py::_check_n1`][resolvers]: it inspects `_prefetched_objects_cache`, `_state.fields_cache`, the planned-resolver set, and the strictness mode — it does NOT inspect `root._state.db`, `queryset._db`, or `router.db_for_read(...)`. Strictness is connection-agnostic by design. Fix: rewrite [Decision 3][spec-023-d3] axis 4, [Goals][spec-023-goals] item 2 (e), [Key glossary references][spec-023-key-glossary-references], and the test wording to say "strictness remains active for objects loaded from any database alias; the package does not re-route the check, and Django owns which alias a lazy load (if permitted) would use; the error class and message are unchanged under non-default aliases." Test sets `root._state.db = 'shard_b'` to prove the object shape is accepted but cannot prove routing (strictness=`raise` prevents the lazy load from happening).
  7. **H7**: rev1's [Decision 6][spec-023-d6] required live `/graphql/` HTTP coverage but then in [Test plan][spec-023-test-plan] allowed in-process `_test_schema.execute_sync(...)` as an alternative. Those are not equivalent contracts; the in-process path skips URL routing, the view, and the Django request pipeline. Per [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" live-query rule, live HTTP is the right tier. Fix: pin one concrete implementation in [Decision 6][spec-023-d6] — `django.test.Client.post("/graphql/", ...)` against a temp URLConf declared in the test module, wrapped with `override_settings(ROOT_URLCONF=<test_module_urlconf>)`, with `clear_url_caches()` in setup / teardown; delete the in-process alternative entirely.
  8. **H8**: rev1's Slice 2 [Test plan][spec-023-test-plan] tests did not declare `@pytest.mark.django_db(databases=...)` access to the `shard_b` alias. Under `pytest-django`, tests that touch a non-default database are blocked unless they declare access via `@pytest.mark.django_db(databases=["default", "shard_b"])` (or `databases="__all__"`). Without the marker, the seed call `models.Book.objects.using("shard_b").create(...)` raises `DatabaseError("...permission to access database 'shard_b'...")`. Fix: pin `@pytest.mark.django_db(databases=["default", "shard_b"])` on each Slice 2 test in [Test plan][spec-023-test-plan].
  9. **H9**: rev1's Slice 2 [Test plan][spec-023-test-plan] said seeding `Book` rows uses "minimal fixtures, no relations needed." Verified against [`examples/fakeshop/apps/library/models.py::Shelf`][models] and [`examples/fakeshop/apps/library/models.py::Book`][models]: `Book.shelf` is a non-null `ForeignKey` to `Shelf`, and `Shelf.branch` is a non-null `ForeignKey` to `Branch`. Seeding a `Book` requires a full `Branch → Shelf → Book` chain. Fix: rewrite the Slice 2 seeding contract in [Test plan][spec-023-test-plan] to spell out the full chain per alias — `Branch.objects.using(alias).create(...)` then `Shelf.objects.using(alias).create(branch=branch, ...)` then `Book.objects.using(alias).create(shelf=shelf, ...)`. The shard-isolation test seeds independent chains on `default` and `shard_b`.
  10. **H10**: rev1's [Decision 6][spec-023-d6] pinned module header showed `import pytest` near the top followed by `import pytest as _pytest_for_fixtures  # noqa: F401` below the skip block. The duplicate import is unnecessary (the same `pytest` name is in scope below the skip), and the `# noqa: F401` contradicts the [Slice checklist][spec-023-slice-checklist] "No `# noqa` suppressions" rule. Fix: rewrite the pinned header to a single `import pytest` placed before the module-level skip block; the autouse fixture below references the same name with no second import needed.
  11. **S11**: rev1's [Slice checklist][spec-023-slice-checklist] Slice 1 sub-bullets said test docstrings are "required by `D102`" and (in [Edge cases][spec-023-edge-cases-and-constraints]) "convention-matching, not gate-forcing." Verified against [`pyproject.toml #"[tool.ruff.lint.per-file-ignores]"`][pyproject]: `per-file-ignores` includes `tests/**/*.py = ["D", "ANN", ...]`, so docstrings and annotations in tests are NOT gate-forced; the "convention-matching" framing is correct, the `D102` claim is wrong. Also the missing-docstring code for free test functions is `D103`, not `D102` (which is class-method-specific). Fix: rewrite the Slice 1 sub-bullets to "Add module and test docstrings to match existing style in `tests/optimizer/` and `tests/types/`. Do not add `# noqa` suppressions for docstring or annotation rules; they are unnecessary under the current per-file ignores."
  12. **S12**: rev1's [`docs/spec-023-multi_db-0_0_7-terms.csv`][spec-023-terms] mapped `Meta.preferred_database` to the `multi-database-cooperation` anchor as a workaround for the absence of a glossary heading. That mis-anchors one concept to a different concept (the cooperation entry covers behavior the package already exhibits; `Meta.preferred_database` is a hypothetical post-`1.0.0` future key tracked in [`BACKLOG.md`][backlog] item 41). Fix: remove the `Meta.preferred_database` row from the CSV; it stays as plain out-of-scope prose in the spec body. If the project later decides to reserve the future-API surface explicitly, that's a new GLOSSARY entry and a new CSV row, not anchor reuse.
  13. **S13**: rev1's [Doc updates][spec-023-doc-updates] → [`KANBAN.md`][kanban] Done-body wording cited the archived path `docs/SPECS/spec-023-multi_db-0_0_7.md` even though the active spec lives at `docs/spec-023-multi_db-0_0_7.md`. The two are correct at different points in the lifecycle: the spec is active at `docs/spec-019-…` while implementation lands, then the archive pass at the end of [`docs/SPECS/NEXT.md`][next] Step 8 moves it to `docs/SPECS/spec-019-…`, after which the [`KANBAN.md`][kanban] Done body is correct. Fix: add an explicit lifecycle note to [Decision 1][spec-023-d1] explaining the active-vs-archived path distinction; the wording in [Doc updates][spec-023-doc-updates] → [`KANBAN.md`][kanban] stays as the archived path because it lands after Step 8 in the close-out flow.
- **Revision 3** (post-rev2 review) — five high-priority consistency fixes (R1–R5) and five medium-priority wording cleanups (R6–R10) that propagate the rev2 narrowed contract into every section that still carried rev1's broader phrasing; surfaced by the rev2 reviewer:
  1. **R1** ([Goals][spec-023-goals] item 1 stale wording): item 1 still listed "`Prefetch` chains respect routing," "`get_queryset` downgrade respects routing," and "strictness mode tracks the originating connection," all of which contradict rev2 H2 / H6. Fix: rewrite [Goals][spec-023-goals] item 1 to enumerate the four narrowed axes verbatim — `router.db_for_read` on FK-id elision stubs, explicit `.using(alias)` preservation through `OptimizationPlan.apply`, consumer-provided `Prefetch(queryset=...)` alias round-trip via `OptimizerHint.prefetch(...)`, and strictness's connection-agnostic shape under non-default aliases.
  2. **R2** (direct `_check_n1` test in the wrong tree): rev2 H4 correctly moved `_build_fk_id_stub` tests to `tests/types/test_resolvers.py`, but the new `test_strictness_check_is_connection_agnostic_under_using` test still lived in `tests/optimizer/test_multi_db.py` while directly exercising `_check_n1` (which also lives in `types/resolvers.py`). The mirror rule applies equally. Fix: move the strictness test into `tests/types/test_resolvers.py` per the mirror rule — Slice 1 becomes five resolver-level tests in `tests/types/test_resolvers.py` (FK-id elision: stub `_state.db` shape, `instance=parent_row`, `instance=None`, null-FK early return; AND strictness connection-agnostic shape) plus two optimizer-plan-level tests in `tests/optimizer/test_multi_db.py` (`OptimizationPlan.apply` preserves `_db`; `OptimizerHint.prefetch(Prefetch(queryset=…))` round-trip). Total: seven pytest items, unchanged. Alternative considered and rejected: routing the strictness test through `DjangoOptimizerExtension(strictness="raise")` + GraphQL execution; that would over-couple a connection-agnostic-shape pin to the extension surface and require a real GraphQL fixture for what is a one-function unit test.
  3. **R3** ([Decision 5][spec-023-d5] heading and body still file-specific): Decision 5 still opened "`tests/optimizer/test_multi_db.py` does NOT depend on `FAKESHOP_SHARDED=1`...", but rev2 H4 split Slice 1 across two files. Fix: rewrite the Decision 5 heading to "Package-internal tests use a fixture router, not `FAKESHOP_SHARDED`" (already true — no rename needed; the body did the heavy lifting) and rewrite the body to refer to "package-internal tests" generally, then enumerate the two files and what they cover. Also soften the [Slice checklist][spec-023-slice-checklist] "Both files mock `router.db_for_read`" — only the router-call tests need the mock; the `OptimizationPlan.apply` test asserts on queryset `_db` and does not exercise FK-id elision.
  4. **R4** (live HTTP harness conflicts with the copied reload fixture): rev2 H7 pinned a module-level `_test_schema` built from a module-level `_MultiDbTestQuery`, but rev2 H7 also kept the [Decision 7][spec-023-d7] copied reload fixture (which clears the registry and reloads `apps.library.schema` / `config.schema` / `config.urls` per autouse run). A module-level `_test_schema` built at import time would hold `DjangoType` classes whose registry entries were cleared by the autouse fixture before the test body runs — producing stale registry/schema interactions. Fix: pin one of two compatible patterns in [Decision 6][spec-023-d6]; preferred path is "build the test schema inside a per-test fixture that runs AFTER the autouse reload, import the freshly-reloaded `BookType` from `apps.library.schema` at fixture time, and route the temp URLConf via a module-level holder pattern (a `_current` dict or class attribute the URLConf reads from at request time)." Alternative pattern documented but not chosen: rebuild `_test_schema` inside each test body before sending the GraphQL request.
  5. **R5** (concrete temp URLConf instructions): rev2 H7's `override_settings(ROOT_URLCONF=<this_module_name>)` was directionally right but left the implementer guessing about the module path. Fix: pin `override_settings(ROOT_URLCONF=__name__)` explicitly with `urlpatterns` declared at module level and `clear_url_caches()` called inside the override-settings context AND in the teardown branch (whether via `try/finally` or a fixture finalizer). The temp URLConf's `path("graphql/", GraphQLView.as_view(schema=…))` reads from the per-test schema holder pattern from R4 so it sees the freshly-built schema rather than a stale one.
  6. **R6** ([Problem statement][spec-023-problem-statement] and [Key glossary references][spec-023-key-glossary-references] over-broaden `get_queryset`): both sections still said "the optimizer's `Prefetch` downgrade for `get_queryset` hooks runs against whatever queryset the consumer's hook returned (which carries its own `_db`)" — which sounds like the root queryset's `_db` flows into the generated child queryset. The accurate framing is narrower: the generated `Prefetch` uses whatever queryset `get_queryset` returned, so if the hook itself explicitly `.using()`-switches the queryset the alias survives; root-queryset alias is NOT threaded. Fix: rewrite both sentences to "if `get_queryset` explicitly returns a `.using(alias)` queryset, that alias survives the downgrade; the root queryset alias is NOT threaded into generated child querysets in this card."
  7. **R7** ([Current state][spec-023-current-state] stub "inherits routing context"): bullet 1 said the stub "inherits the routing context of the parent row when one exists" — that's a downstream consequence of the router's behavior, not the package's contract. Fix: rewrite to "consumer routers can consult the parent row as an `instance=` hint; the stub's `_state.db` is whatever the router returns from that call."
  8. **R8** ([Decision 3][spec-023-d3] justification cites old KANBAN bullets): the justification paragraph after the four axes said "the four-axis list maps 1-to-1 to the KANBAN card's 'Confirm …' bullets (router cooperation; optimizer plan correctness under `.using()`; strictness mode tracking originating connection; `get_queryset` downgrade respecting routing)" — the last two bullets reflect the KANBAN's pre-narrowing language. Fix: add a parenthetical noting that the KANBAN wording is interpreted through the rev2-narrowed contract (strictness remains active but does not route; generated `get_queryset` prefetches do not inherit the root alias).
  9. **R9** (Doc-update snippets reintroduce broad wording): the planned [`docs/README.md`][readme] forward-pointer wording and the planned [`docs/GLOSSARY.md`][glossary] four-axis body update still said "what the package guarantees under `.using()`, `Prefetch` chains, and `get_queryset` downgrades" — reviving the rev1 broad framing. Fix: rewrite both snippets to enumerate the rev2-narrowed axes explicitly (explicit `.using()` preservation; FK-id elision router hints; consumer-provided `Prefetch(queryset=...)` aliases; strictness behavior under non-default aliases) so the doc updates land with consistent wording.
  10. **R10** ([Decision 1][spec-023-d1] lifecycle note is overcomplicated): rev2 S13's lifecycle note claimed the KANBAN Done body cites the archived path because the close-out flow happens after Step 8 of the next spec-author's NEXT.md run — but implementation close-out and spec-author Step 8 are separate workflows in practice, and the simpler rule is "references point to wherever the file actually is when the edit happens." Fix: simplify the lifecycle note to "while this spec is the active in-flight spec, references use `docs/spec-023-multi_db-0_0_7.md`; after a future archive pass moves it under `docs/SPECS/`, references use `docs/SPECS/spec-023-multi_db-0_0_7.md`; the [`KANBAN.md`][kanban] Done body uses whichever path is current at the time of that edit." Do not imply the implementation Slice 3 runs after a hypothetical future-card NEXT.md Step 8.
- **Revision 4** (post-rev3 review) — three High correctness blockers (V1–V3), two Medium doc/wording-drift fixes (V4–V5), and three Low polish items (V6–V8); all surfaced by the rev3 reviewer:
  1. **V1** (`plan_optimizations()` signature drift): rev2 H3 / rev3 R2 corrected the call-shape framing but the pinned test wording still said `plan_optimizations(selections, model, parent_type)`. Verified against [`optimizer/walker.py::plan_optimizations`][walker]: the real signature is `plan_optimizations(selected_fields, model, info=None, *, source_type=None)`. The third positional is `info`, NOT a parent-type — Worker 2 writing the rev3 form would silently bind `parent_type` (a class) to `info`, then the walker would later call `info.path` and crash. Fix: rewrite the [Test plan][spec-023-test-plan] test (f) and the [Edge cases][spec-023-edge-cases-and-constraints] clarifier to call `plan = plan_optimizations(selected_fields, model)` (simplest — test (f) does not exercise per-type hint lookup; that's test (g)) or `plan_optimizations(selected_fields, model, source_type=parent_type)` if a parent type is needed; also rename `selections` to `selected_fields` everywhere to match the live parameter name.
  2. **V2** (`kind="many_to_one"` is not a valid `RelationKind`): rev2 H6 / rev3 R2 pinned the strictness test setup as `_check_n1(..., kind="many_to_one")`. Verified against [`utils/relations.py #"RelationKind: TypeAlias"`][relations] that `RelationKind` is `Literal["many", "reverse_many_to_one", "reverse_one_to_one", "forward_single"]` — `"many_to_one"` is not one of them. `_check_n1` accepts any string at runtime, but `is_many_side_relation_kind("many_to_one")` returns `False` (the membership set is `{"many", "reverse_many_to_one"}` per [`utils/relations.py #"MANY_SIDE_RELATION_KINDS"`][relations]), so the rev3 `_prefetched_objects_cache = {}` setup is meaningless (the call falls through to `_will_lazy_load_single`, which reads `__dict__` and `_state.fields_cache`, not the prefetch cache). Fix: change `kind="many_to_one"` to `kind="forward_single"` in [Goals][spec-023-goals] item 2 (e), [Slice checklist][spec-023-slice-checklist], and [Test plan][spec-023-test-plan] test (e); FK lazy-load on a `_state.db = "shard_b"` row is the natural illustration.
  3. **V3** (setup-mismatch — `_prefetched_objects_cache = {}` on a `forward_single` test): a direct consequence of V2 — once `kind="forward_single"` is fixed, the lazy-load detector branches into `_will_lazy_load_single` at [`types/resolvers.py::_will_lazy_load_single`][resolvers], which inspects `__dict__` and `_state.fields_cache`, not `_prefetched_objects_cache`. Fix: rewrite the test (e) setup pin to: "ensure `field_name not in root.__dict__` and `field_name not in root._state.fields_cache` so `_will_lazy_load_single` reports the relation is unloaded; set `root._state.db = 'shard_b'` to prove the connection-agnostic shape; do NOT set `root._prefetched_objects_cache` — the single-valued path does not consult it."
  4. **V4** ([Doc updates][spec-023-doc-updates] → [`KANBAN.md`][kanban] Done-body / [`CHANGELOG.md`][changelog] entry stale counts): the rev2 Done-body wording still said "four resolver-level tests against `_build_fk_id_stub` … three optimizer-plan-level tests against `OptimizationPlan.apply` and `OptimizerHint.prefetch` round-trip and `_check_n1`" — both the counts and the "and `_check_n1`" parenthetical are stale post-rev3 R2 (the strictness test moved out of `tests/optimizer/test_multi_db.py`). The CHANGELOG entry carried the same "/ strictness shape" leftover. Fix: rewrite the KANBAN Done-body parenthetical to "five resolver-level tests against `_build_fk_id_stub` and `_check_n1` — four FK-id elision branches plus the strictness connection-agnostic shape; FK-id tests hermetic via mocked router" and "two optimizer-plan-level tests against `OptimizationPlan.apply` and `OptimizerHint.prefetch` round-trip"; rewrite the CHANGELOG entry's optimizer-plan parenthetical to drop "/ strictness shape" and add `_check_n1` to the resolver-level tree's coverage list.
  5. **V5** ([Edge cases and constraints][spec-023-edge-cases-and-constraints] plan-cache + consumer-`Prefetch` interaction): the rev2 edge-case clarifier on the plan cache key correctly says cache keys do NOT include the queryset's `_db`, but did not explicitly address how that composes with [Decision 3][spec-023-d3] axis 3 (consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…using…))` round-trips). The cached plan can contain a `Prefetch` object bound to `shard_b`; if two resolvers shared the cache key but wanted different shards on the child relation, the second would silently get the first's alias. Verified at [`plans.py::resolver_key`][plans] that `resolver_key(parent_type, …)` includes the parent type in the cache key, and [`Meta.optimizer_hints`][glossary-metaoptimizer-hints] is per-`DjangoType`, so two resolvers using the same parent type necessarily share the same hint config — the invariant holds. Fix: add one sentence to the existing plan-cache edge-case clarifier to pin the type-scoped binding and explain why no per-call leak is possible.
  6. **V6** ([Decision 6][spec-023-d6] header `importlib` / `sys` imports unexplained): the pinned module-header code block imports `importlib`, `os`, `sys`, `pytest` at the top but the prose below it does not say where `importlib` / `sys` are used. Verified at [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`][test-library-api]: the copied autouse reload fixture uses `sys.modules.get(...)` + `importlib.reload(...)` / `importlib.import_module(...)`. Fix: append a one-line annotation under the pinned-shape block stating that the `importlib` / `sys` imports support the copied autouse reload fixture per [Decision 7][spec-023-d7] — so the next reader does not flag them as unused.
  7. **V7** ([Implementation plan][spec-023-implementation-plan] row-1 annotation missed the rev3 R2 callout): the [Slice checklist][spec-023-slice-checklist] bullets carry the rev3 R2 annotation correctly, and the spec-body Decision text says "rev3 R2 — strictness test relocated", but the table cell's per-revision annotation list jumped from "Rev2 H6" to "Rev3 R2" without explicitly naming the strictness move. Fix: confirm the table row's annotation already names the move (verified at the [Implementation plan][spec-023-implementation-plan] row-1 annotation — "Rev3 R2 — strictness test relocated from `tests/optimizer/test_multi_db.py` to `tests/types/test_resolvers.py` because `_check_n1` lives in `types/resolvers.py`") and treat this as already-correct; this rev4 entry catalogs that the sweep checked it.
  8. **V8** ([Decision 7][spec-023-d7] clause "additional early-module-skip guard" reads cleanly already): no change required; the rev3 reviewer flagged a possible double-take but the existing word "additional" makes the additive relationship explicit, so the wording stays.
- **Revision 5** (post-rev4 review) — one High correctness blocker (X1: off-by-one axis-to-test letter cross-references), two Medium doc-drift fixes (X2–X3 — same off-by-one in [Edge cases][spec-023-edge-cases-and-constraints] and [Risks][spec-023-risks-and-open-questions] cross-references), and three Low implementer-friction items (X4–X6); all surfaced by the rev4 reviewer's pre-build TODO scaffold pass:
  1. **X1** ([Decision 3][spec-023-d3] axes 2/3/4 cross-references still use the rev2-era letter mapping): rev3 R2 relocated the strictness test from `tests/optimizer/test_multi_db.py` to `tests/types/test_resolvers.py`, which shifted the letter mapping — the strictness test is now (e) in the resolver-level file, the `OptimizationPlan.apply` test is now (f) in the optimizer-plan file, and the consumer-`Prefetch` test is now (g) in the optimizer-plan file. The [Slice checklist][spec-023-slice-checklist], [Goals][spec-023-goals] item 2, [Test plan][spec-023-test-plan], and [Definition of done][spec-023-definition-of-done] item 2 all use the corrected post-rev3 numbering; the [Decision 3][spec-023-d3] per-axis "Verified by" cross-references were missed by the rev4 V7 sweep and still cite rev2's (e/f/g) → (axis 2/axis 3/axis 4). Worker 2 reading axis 4 = "optimizer-plan test (g)" would either silently put the strictness test back in `tests/optimizer/test_multi_db.py` (undoing rev3 R2 mid-implementation) or have to chase three spec sections to reconstruct the intended mapping. Fix: rewrite the three "Verified by" sentences in [Decision 3][spec-023-d3] axes 2 / 3 / 4 to the longer "Verified by Slice 1's <layer> test (<letter>) — `<test_name>` in `<file>`" form. The longer form kills the off-by-one bug class outright by naming the test rather than relying on a positional letter that drifts across revisions.
  2. **X2** ([Edge cases][spec-023-edge-cases-and-constraints] "Consumer-provided `Prefetch(queryset=...)` `_db` round-trip" bullet cites the wrong test letter — same drift as X1): the bullet says "Slice 1's optimizer-plan test (f) introspects the post-plan `_prefetch_related_lookups`," but the consumer-`Prefetch` introspection is test (g); test (f) is the `OptimizationPlan.apply`-preserves test (axis 2), which asserts on `result._db` rather than on `_prefetch_related_lookups`. Fix: change "test (f)" to "test (g)" in this bullet.
  3. **X3** ([Risks][spec-023-risks-and-open-questions] "Consumer-provided `Prefetch(queryset=...)` `_db` round-trip under Django version changes" bullet cites the wrong test letter): the bullet says "The Slice 1 optimizer-plan test (f) pins the package's cooperation by introspecting the post-plan `_prefetch_related_lookups`" — same drift as X2. Fix: change "test (f)" to "test (g)".
  4. **X4** ([Decision 6][spec-023-d6] pinned import block lists names the test module doesn't use): the pinned header imports `DjangoOptimizerExtension`, `DjangoType`, and `finalize_django_types` from the package, but the holder-pattern + per-test-fixture pseudocode below uses only `DjangoOptimizerExtension`. `BookType` is imported from `apps.library.schema` INSIDE the `_build_test_schema` fixture (rev3 R4) and is already a finalized `DjangoType`; the test module never declares a `DjangoType` subclass or calls `finalize_django_types()` itself. Worker 2 landing the file verbatim would either ship F401-flagged unused imports (and need a `# noqa: F401` that violates the no-suppression rule) or silently drop them and diverge from the spec's pinned shape. Fix: trim the package import in the pinned header to `from django_strawberry_framework import DjangoOptimizerExtension`, and add a short annotation matching the rev4 V6 style explaining why `DjangoType` / `finalize_django_types` are NOT imported at the test-module level.
  5. **X5** ([Test plan][spec-023-test-plan] `tests/types/test_resolvers.py` section silent on `FieldMeta` construction shape): tests (a)-(d) all construct a `FieldMeta` instance to pass to `_build_fk_id_stub(root, field_meta)`, but the spec doesn't pin which `FieldMeta` constructor arguments are required vs optional — Worker 2 has to read [`optimizer/field_meta.py`][field-meta] to know the dataclass shape. Fix: add two sentences to the [Test plan][spec-023-test-plan] `tests/types/test_resolvers.py` section pinning the construction pattern — direct `FieldMeta(...)` construction (NOT `FieldMeta.from_django_field`) with the required-for-FK-id-elision arguments `name`, `is_relation=True`, `related_model`, and `attname`; every other field has a default sufficient for this test surface.
  6. **X6** ([Test plan][spec-023-test-plan] `tests/optimizer/test_multi_db.py` section silent on synthetic `selected_fields` shape): tests (f) and (g) call `plan_optimizations(selected_fields, model, ...)` with synthetic selection-tree nodes, but the spec doesn't pin the shape (the walker reads `.name` / `.alias` / `.directives` / `.selections` at minimum via `_walk_selections` / `_included_field_selections` / `_merge_aliased_selections`). [`tests/optimizer/test_walker.py`][test-walker] and [`tests/optimizer/test_plans.py`][test-plans] already have a working `SimpleNamespace`-based selection-builder pattern. Fix: add one sentence to the [Test plan][spec-023-test-plan] `tests/optimizer/test_multi_db.py` section telling Worker 2 to mirror the existing fixture pattern rather than invent a new one.

## Decision 1 — Spec filename and canonical naming

Spec text: [Decision 1][spec-023-d1]. Contract that stays: the spec lives at the structured `spec-023-multi_db-0_0_7.md` name, and references point at whichever path the file actually has when the reference is written.

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 and proven by every recent spec ([`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018], [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019], [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020], [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021], [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022]) bakes the card's NNN and target patch into the filename. The card body's `docs/spec-multi_db.md` predates that convention and would land an unnumbered spec next to a numbered cohort, breaking the alphabetical archive ordering at `docs/SPECS/`.
- The Slice 3 [`KANBAN.md`][kanban] update overwrites the stale `docs/spec-multi_db.md` reference in the card body to point at the canonical name, so the cross-reference resolves after archival (per [Step 8 of NEXT.md][next-step-8--archive-prior-specs-and-update-cross-references]).
- This Decision is enforcement, not innovation: the convention is already pinned in [`docs/SPECS/NEXT.md`][next] Step 6 and observed by every spec from 014 forward.

### Alternatives considered (and rejected)

- **Honor the card body verbatim with `docs/spec-multi_db.md`.** Rejected: would diverge from the structured naming convention; would force a Step-8 archive rename anyway; would not match the [`KANBAN.md`][kanban] sibling cards' filenames in the WIP / Done columns.
- **Ship as `docs/spec-019-multi-db-0_0_7.md` (hyphen separator in the topic slug).** Rejected: every prior spec uses snake_case for the topic slug (`list_field`, `meta_primary`, `consumer_overrides_scalar`, `export_schema`, `apps`, `deferred_scalars`). `multi_db` matches the convention; `multi-db` would be a one-spec outlier.

### Changes this Decision underwent

- **rev2 S13** added a lifecycle note distinguishing the active `docs/spec-023-…` path from the archived `docs/SPECS/spec-023-…` path, and justified the [`KANBAN.md`][kanban] Done body citing the archived path by asserting that the close-out flow runs after a future spec-author's [`NEXT.md`][next] Step 8.
- **rev3 R10** rejected that reasoning: implementation close-out and a spec-author's Step 8 are independent workflows in this repo, and the simpler rule is "references point to wherever the file actually is when the edit happens." The lifecycle note was rewritten to that rule and the Step-8 sequencing claim was dropped. The surviving note in the spec is rev3's.

### Claims this Decision may no longer make

- That implementation Slice 3 runs after a hypothetical future-card `NEXT.md` Step 8 (retracted by rev3 R10).
- That the spec is the *active* in-flight document at `docs/spec-023-multi_db-0_0_7.md`. The archive has happened; the file is at `docs/SPECS/spec-023-multi_db-0_0_7.md` and its terms CSV at `docs/SPECS/appx/`. Slice 2 re-pointed the spec's prose accordingly; `docs/spec-023-multi_db-0_0_7.md` now has 0 occurrences in the spec.

## Decision 2 — No production code change

Spec text: [Decision 2][spec-023-d2]. Contract that stays: the card ships zero production code change; the cooperation surface already exists in source.

### Justification (moved from the spec)

- [`KANBAN.md`][kanban] card body: "Status: planned. **The cooperation already exists in source; this card pins the contract with a spec, tests, and docs.**" The card explicitly frames this as a documentation + tests card.
- The cooperation is grep-verifiable: `grep -rn "router\.\|\.using\b\|_state\.db\b" django_strawberry_framework/` returns one production line ([`types/resolvers.py::_build_fk_id_stub`][resolvers]) and zero other touchpoints; the optimizer's cooperation rides on queryset `_db` propagation, which is a Django queryset contract, not a package one.
- Pinning a contract with tests is the cheapest way to prevent regression. Adding production code (e.g., a `router.allow_relation` consultation, a `Meta.preferred_database` hint) would expand the surface beyond what the contract actually documents and would re-litigate the [`BACKLOG.md`][backlog] item 41 boundary.

**Time-scope warning on the second bullet.** "returns one production line … and zero other touchpoints" was true of the package at `0.0.6`, when the card was written. It is false of `HEAD`: `router.db_for_read` / `db_for_write` are additionally called from `django_strawberry_framework/utils/permissions.py #"aliases = {router.db_for_read(model)"` and twice in `django_strawberry_framework/utils/write_transaction.py` — four `router.db_for_*` call sites in all — and `.using(` is called in 9 package modules (13 mention the token; four mention it only in docstrings or error strings). The `0.0.11`-`0.0.14` write family and the visibility-boundary hardening added them, all after this card shipped. The bullet is preserved verbatim as the scope statement it was; it is not a description of `HEAD`.

### Alternatives considered (and rejected)

- **Add a `router.allow_relation(obj1, obj2)` consultation in the FK-id elision path.** Rejected: `allow_relation` is for cross-DB foreign-key validity; FK-id elision happens within a single connection, so calling it would be a no-op (Django's queryset cross-shard validation already runs at queryset evaluation, before the optimizer sees the row).
- **Add a `Meta.preferred_database` hint for routing.** Rejected: covered by [`BACKLOG.md`][backlog] item 41; pre-shipping it would impose API surface this card does not have evidence to design correctly.
- **Refactor `_build_fk_id_stub` to read `instance=parent_row` through a helper.** Rejected: the current code is six lines and reads cleanly; introducing a helper for one call site would be over-abstraction.

**Time-scope warning on the third rejected alternative.** "the current code is six lines" described `_build_fk_id_stub` at `0.0.6`. At `HEAD` the body carries an additional `_FK_ELISION_UNSAFE` early return for a deferred `attname`, so the line count and the "one call site" framing are both stale. The *conclusion* — do not extract a helper for it — is untouched by that.

### Changes this Decision underwent

- **rev1** established the zero-production-code scope from the [`KANBAN.md`][kanban] card body.
- **rev2 H2** confirmed the boundary in the other direction: threading the parent queryset's `_db` into generated child querysets is exactly the production-code expansion this Decision defers, and it was routed to [`BACKLOG.md`][backlog] item 41 rather than into the card.

## Decision 3 — The cooperation contract: four axes

Spec text: [Decision 3][spec-023-d3]. Contract that stays: the four axes and the four out-of-scope items beneath them.

### Justification (moved from the spec)

- The four-axis list maps 1-to-1 to the [`KANBAN.md`][kanban] card's "Confirm …" bullets (router cooperation; optimizer plan correctness under `.using()`; strictness mode tracking originating connection; `get_queryset` downgrade respecting routing). Pinning the axes here lets the test plan target one test per axis with no gaps. **The KANBAN wording is interpreted through the rev2-narrowed contract (rev3 R8):** strictness remains active for non-default-aliased rows but the check is connection-agnostic — it does NOT route — and generated `get_queryset` `Prefetch` child querysets do NOT inherit the root queryset's alias (consumer-provided `Prefetch(queryset=…)` via `OptimizerHint.prefetch(...)` is the supported route). The KANBAN's pre-narrowing wording is preserved as the cross-reference target; the implementation contract is the narrower one.
- Anything not on the list is either an in-scope behavior the package already exhibits via Django's queryset contract (and therefore needs no package-level pinning) or an out-of-scope future-card concern.

This Decision never carried an `Alternatives considered (and rejected):` list; its rejected alternatives are the axes rev2 refused to widen, recorded below.

### Changes this Decision underwent

- **rev1** stated four axes in broad form: "`Prefetch` chains respect routing", "`get_queryset` downgrade respects routing", and "strictness mode tracks the originating connection".
- **rev2 H1** deleted the claim that "the `_db` attribute is set on the queryset before the optimizer's plan application". Verified false against Django's queryset semantics: an implicit-router queryset keeps `_db is None` until evaluation. Axis 2 was rewritten to say the package preserves an *explicit* `.using()` alias and leaves an implicit one alone.
- **rev2 H2** narrowed axis 3. "`Prefetch` chains respect routing" was verified false against `_build_child_queryset`, which starts from `field.related_model._default_manager.all()` and never threads the root alias. Axis 3 now promises only that a *consumer-provided* `Prefetch(queryset=…)` round-trips with its own `_db`.
- **rev2 H6** narrowed axis 4. "strictness mode tracks the originating connection" was verified false against `_check_n1`, which never reads `root._state.db`, `queryset._db`, or the router. Axis 4 now says strictness is connection-agnostic.
- **rev3 R1** propagated the two narrowings into `## Goals` item 1, which had kept rev1's wording.
- **rev3 R6** narrowed the `get_queryset` framing in `## Problem statement` and `## Key glossary references`: the hook's own `.using()` survives the downgrade; the root alias does not flow into generated children.
- **rev3 R8** added the note that the [`KANBAN.md`][kanban] card's pre-narrowing "Confirm …" bullets are read *through* the narrowed contract rather than at face value.
- **rev5 X1** replaced the per-axis "Verified by test (letter)" cross-references with the longer "Verified by Slice 1's `<layer>` test (`<letter>`) — `<test_name>` in `<file>`" form, after rev3 R2's relocation of the strictness test shifted the letter mapping and left axes 2 / 3 / 4 pointing at the wrong tests. Naming the test rather than the position is what kills that bug class.

### Claims this Decision may no longer make

- That `Prefetch` chains generally respect routing (rev2 H2).
- That strictness mode tracks the originating connection (rev2 H6).
- That the optimizer sets `_db` on a queryset before plan application (rev2 H1).
- **Axis 3's flat "generated `Prefetch` querysets do NOT inherit the parent queryset's `_db`" is now time-qualified at `HEAD`.** It still holds at plan-construction, but later nested-connection machinery threads the parent alias at *fetch* time (`optimizer/single_parent_fetch.py #"child_qs = spec.pristine_child_queryset.using(queryset.db)"`, `optimizer/nested_planner.py #"correct alias-late predicate at fetch time"`, `filters/sets.py #"child_manager.using(parent_db).all()"`). Slice 2 added the qualifier at all seven spec sites; see `### D2 — axis 3 is alias-LATE, not alias-absent`.

## Decision 4 — No routing decoration on fakeshop schemas

Spec text: [Decision 4][spec-023-d4]. Contract that stays: the fakeshop app schemas are not modified; the live tests bring their own schema.

### Justification (moved from the spec)

- Routing policy is consumer-shaped (per [Decision 3][spec-023-d3]); a fakeshop schema with hard-coded `.using("shard_b")` would be misleading example code suggesting routing is the package's call. The default fakeshop schemas should continue to demonstrate the simplest possible Strawberry surface, which is single-DB.
- The live test's purpose is to prove cooperation under the existing `FAKESHOP_SHARDED=1` infrastructure, not to redesign the example schemas.
- Mirrors the [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] Decision 9 posture for `DjangoListField` (added a fakeshop demonstration as a *sibling* root field rather than rewriting existing list-resolver schema entries).

### Alternatives considered (and rejected)

- **Add a `books_on_shard_b: list[BookType]` sibling resolver to `apps/library/schema.py`.** Rejected: would clutter the example app schema with a multi-db demonstration that only triggers under `FAKESHOP_SHARDED=1`; the routing would always read from `shard_b` regardless of env var, which is wrong under single-DB mode (where `shard_b` doesn't exist in `DATABASES`).
- **Add `DATABASE_ROUTERS` to `examples/fakeshop/config/settings.py`.** Rejected: would impose a routing opinion on the example project; consumers exercising the existing single-DB and sharded modes don't need a router class.

### Changes this Decision underwent

None. The Decision was stated in rev1 and no revision touched it. The `_MultiDbTestQuery` / holder-pattern machinery that satisfies it was settled under [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) instead.

## Decision 5 — Package-internal tests use a fixture router, not `FAKESHOP_SHARDED`

Spec text: [Decision 5][spec-023-d5]. Contract that stays: the two-file split, what each file covers, and the pinned mock target.

### Justification (moved from the spec)

- Package-internal tests must be runnable without any fakeshop-side env var. The test suite already runs against a single SQLite by default; introducing a real second SQLite would (a) require materializing it before the test runs, (b) require teardown logic to avoid polluting the dev `db.sqlite3`, (c) double the per-test cost without testing anything the targeted assertion doesn't catch.
- The router-call contract is "we call `router.db_for_read` with this signature and this `instance` argument" — that's a router-call assertion, not a routing-outcome assertion. The router's outcome (which alias gets returned) is consumer-shaped; the package's contribution is the call itself. Mock the router and assert on the call shape.
- The queryset-`_db` and `Prefetch`-`_db` contracts are direct queryset-attribute assertions; they don't go through the router and don't need a mock.
- The fakeshop live test in Slice 2 is what exercises a real second connection end-to-end. The two test layers compose: Slice 1 pins the package's per-function contracts in isolation; Slice 2 pins the end-to-end cooperation under a real router policy and a real second connection.

### Alternatives considered (and rejected)

- **Run package-internal tests under a real two-DB SQLite layout.** Rejected: cost / setup / teardown burden, and the assertion granularity is worse (a router-call assertion catches a regression where the call is dropped, even when the alias outcome happens to match the default).
- **Mock `router.db_for_read` globally via `django.db.router.db_for_read`.** Rejected: monkey-patching the global would leak to other tests in the suite. The module-level alias inside `types.resolvers` is the right scope.
- **Mock `router.db_for_read` in every Slice 1 test, including the strictness and optimizer-plan tests.** Rejected per rev3 R3: the strictness and optimizer-plan tests don't exercise FK-id elision and adding a mock would be over-broad — a regression in those code paths would no-op the mock without changing the assertion's outcome.

### Changes this Decision underwent

- **rev2 H4** split Slice 1 across two files. rev1 had lumped `_build_fk_id_stub` and `_check_n1` tests into `tests/optimizer/test_multi_db.py`, but both functions live in `types/resolvers.py` and [`docs/TREE.md`][tree]'s mirror rule puts their unit tests in `tests/types/test_resolvers.py`. The [`KANBAN.md`][kanban] card body names only the optimizer file; the resolver file is an additive companion, and the split was stated explicitly so a later maintainer would not reverse it.
- **rev2 H5** split one conflated test into two. rev1 described "returns `None` for a `None` FK (the `instance` arg is forwarded as `None` when the parent row has no `_state`)" as a single case; the null FK takes an early `return None` *before* the router is called, while parent-lacks-`_state` reaches the router with `instance=None`. Different code paths, different regressions, two tests.
- **rev3 R2** relocated the strictness test out of `tests/optimizer/test_multi_db.py`, which rev2 H4 had left behind: `_check_n1` also lives in `types/resolvers.py`, so the mirror rule applies to it equally. Slice 1 became five resolver-level tests plus two optimizer-plan-level ones. A further alternative was considered and rejected there — routing the strictness test through `DjangoOptimizerExtension(strictness="raise")` plus real GraphQL execution — because it would over-couple a connection-agnostic-shape pin to the extension surface and demand a GraphQL fixture for a one-function unit test.
- **rev3 R3** rewrote the Decision body from rev2's single-file framing to the two-file enumeration, and softened "both files mock `router.db_for_read`" to "only the four FK-id-elision tests do" — the strictness and optimizer-plan tests never reach the elision path, and mocking there would be over-broad.
- **The optimizer file later dropped to one test.** The shipped `tests/optimizer/test_multi_db.py` carries only the consumer-`Prefetch` round-trip; axis 2's `OptimizationPlan.apply` assertion was folded into the Slice 2 live HTTP test under the [`AGENTS.md`][agents] real-usage rule, taking Slice 1 from seven pytest items to six.

## Decision 6 — Live coverage under `FAKESHOP_SHARDED=1`

Spec text: [Decision 6][spec-023-d6]. Contract that stays: the collection-time skip, the pinned module header and its two import annotations, the holder-pattern URLConf, the per-test schema fixture, and the five-step per-test shape. **This Decision's `Justification:` block also stays in the spec** — see `## Provenance of this record`.

### Alternatives considered (and rejected)

- **`pytest.mark.skipif(...)` on each test.** Rejected per the module-import-time `DATABASES` decision above.
- **`pytest.mark.skipif(...)` on the test class.** Rejected for the same reason; mark evaluation happens after import.
- **Move the entire test into `examples/fakeshop/tests/` (non-HTTP).** Rejected: the cooperation surface this test pins is end-to-end through `/graphql/`, including the URL routing, view, schema execution, and JSON serialization; the `test_query/` tree is the right home. The package-internal Slice 1 tests are the non-HTTP layer.
- **In-process `_test_schema.execute_sync(...)`.** Rejected per rev2 H7 — the live HTTP rule in [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" governs. Rev1 had this as an acceptable alternative; rev2 deletes it.
- **Build a module-level static `_test_schema` at import time** (rev2 H7's original shape). Rejected per rev3 R4: the autouse reload fixture clears the registry and reloads `apps.library.schema` before each test runs, so a module-level static `_test_schema` would reference `DjangoType` classes whose registry entries have been cleared — producing stale-schema bugs. The holder pattern above defers schema construction to AFTER the reload.
- **Rebuild `_test_schema` inside each test body before sending the request** (alternative explored under rev3 R4). Rejected as primary pattern in favor of the per-test fixture (which is the same construction logic factored into a reusable place); test bodies stay focused on the assertion shape, not the harness wiring.

### Changes this Decision underwent

- **rev2 H7** deleted the in-process `_test_schema.execute_sync(...)` escape hatch rev1 had allowed alongside live HTTP. They are not equivalent contracts: the in-process path skips URL routing, the view, and the Django request pipeline that [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" names as the right tier. One concrete implementation was pinned instead.
- **rev2 H10** removed a duplicate `import pytest as _pytest_for_fixtures  # noqa: F401` from the pinned header. The same `pytest` name is already in scope below the skip block, and the suppression contradicted the Slice checklist's no-`# noqa` rule.
- **rev3 R4** resolved a conflict rev2 H7 had created with [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest): a module-level `_test_schema` built at import time would hold `DjangoType` classes whose registry entries the autouse reload fixture clears before the test body runs. The holder pattern — a module-level mutable holder the temp URLConf's view reads per request, filled by a per-test fixture that depends on the reload fixture — was pinned as the primary shape.
- **rev3 R5** replaced rev2's vague `override_settings(ROOT_URLCONF=<test_module_urlconf>)` placeholder with `ROOT_URLCONF=__name__`, module-level `urlpatterns`, and `clear_url_caches()` both on entering the override context and in teardown.
- **rev4 V6** annotated the pinned header's `importlib` / `sys` imports as supporting the copied reload fixture, so a later reader would not flag them unused.
- **rev5 X4** trimmed the pinned package import to `DjangoOptimizerExtension` alone. `DjangoType` and `finalize_django_types` were listed but never used at module level: `BookType` is imported inside the fixture after the reload, and `finalize_django_types()` runs in the reloaded `apps.library.schema` module body. Landing the header verbatim would have shipped two `F401`s and forced the forbidden `# noqa`.
- **rev5-post X7** widened the isolation test's GraphQL query from `{ title }` to the full `{ title shelf { code branch { name } } }` shape. Under the optimizer's `only(...)` projection, a `{ title }`-only selection against the spec-pinned `.select_related("shelf__branch")` resolver produces `Book.objects.only("title", "shelf_id").select_related("shelf__branch")`, which Django rejects with `FieldError: Field Book.shelf cannot be both deferred and traversed using select_related at the same time`. Widening the query kept the pinned resolver shape (required by [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas)) and moved the negative assertion onto the returned `title` set rather than onto selection narrowness.

### Claims this Decision may no longer make

- That in-process `execute_sync(...)` is an acceptable alternative to live HTTP for this surface (rev2 H7).
- That a module-level static `_test_schema` is a workable shape (rev3 R4).
- That `examples/fakeshop/test_query/test_multi_db.py` holds two tests and imports only `DjangoOptimizerExtension` from the package. At `HEAD` the file holds ten tests — debug-extension alias capture, row-preserving predicates on `shard_b`, and the `0.0.14` model- and serializer-flavor write-alias suites. Reconciling the pinned import header and the exhaustive two-test reading is Slice 2's.

## Decision 7 — The reload fixture comes from the shared `test_query` conftest

Spec text: [Decision 7][spec-023-d7]. Contract that stays: the multi-db module depends on the tree's one autouse registry-reload fixture rather than declaring its own.

**The heading and the contract sentence both changed in Slice 2.** The Decision originally read *Reuse the `test_library_api` reload fixture verbatim*, and its contract was "copy the fixture, do not pre-emptively factor." The justification below names the condition that would justify extracting it — "a `conftest.py` shared across `test_query/` files, justified once 2+ files need it" — and that condition has since been met: [`examples/fakeshop/test_query/conftest.py`][test-query-conftest] defines the module-scoped autouse `_reload_project_schema_for_acceptance_tests`, no module in the tree carries a private copy, and `test_multi_db.py` reaches it by depending on it from `_build_test_schema`. The Decision's own escape clause fired, so the spec states the shipped source of the fixture. Renaming the heading moved this file's anchor and the spec's eight in-page uses of it; both were rewritten in the same pass.

### Justification (moved from the spec)

- The fixture is required for any test that runs after a package test that clears the registry; the multi-db tests are no exception.
- Copying the fixture verbatim (rather than moving it to a conftest.py) keeps the fixture local to the file that needs it; the test file's first ~30 lines remain self-contained and a reader does not have to chase a sibling file.
- The trade-off is duplicated code, but the fixture is small (~25 lines) and copying it follows the existing fakeshop test-tree pattern (the README at `examples/fakeshop/test_query/README.md` does not specify a shared `conftest.py`, and `test_library_api.py` is the only existing `test_query/` test file).
- If a future card moves the fixture to a `conftest.py` shared across `test_query/` files (justified once 2+ files need it), the move is a Definition-7 follow-up under its own spec. The boundary is "do not pre-emptively factor."

### Alternatives considered (and rejected)

- **Move the fixture to `examples/fakeshop/test_query/conftest.py` and let both files autouse it.** Rejected per the "do not pre-emptively factor" boundary; the conftest-extraction is justified by a second test file needing it, and this spec's job is to add that second file, not to settle the factoring question.
- **Skip the reload fixture and hope tests run in a friendly order.** Rejected: registry-clearing package tests run before `examples/fakeshop/test_query/` tests in pytest's discovery order, so the fixture is load-bearing for the test suite to pass.

### Changes this Decision underwent

- **rev4 V8** examined the clause "with an additional early-module-skip guard" for a possible double-take and left it unchanged: "additional" already makes the additive relationship explicit. Recorded because the sweep checked it, not because anything moved.

### Claims this Decision may no longer make

- **Its whole justification rests on `test_library_api.py` being the only file in `examples/fakeshop/test_query/`, and on there being no shared `conftest.py`.** Neither is true at `HEAD`: the tree holds 21 test modules plus `examples/fakeshop/test_query/conftest.py` — the exact conftest extraction this Decision deferred to "a future card, once 2+ files need it". The deferral was discharged; the justification above is a snapshot of `0.0.7` and is kept as the reasoning that was applied, not as a description of the tree.
- **That the module copies the fixture verbatim.** It does not; it depends on the shared one. Reconciled in the spec by Slice 2 (heading and body both).

## Decision 8 — No README / GOAL / TODAY edits

Spec text: [Decision 8][spec-023-d8]. Contract that stays: the three root docs are not edited, and the one user-facing breadcrumb is the [`docs/README.md`][readme] line.

### Justification (moved from the spec)

- The README's status section names consumer-facing primitives ([`DjangoType`][glossary-djangotype], the optimizer, [`DjangoListField`][glossary-djangolistfield]); the multi-database cooperation contract is plumbing the package already honors, not a new consumer-name surface.
- `GOAL.md`'s astronomy showcase walks through model definitions and the sidecar files (`filters.py`, `orders.py`, `aggregates.py`, `fields.py`); none of which is multi-db-specific. The migration shape section names `graphene-django` / `strawberry-graphql-django` / DRF + django-filter migrants, none of which leans on multi-db cooperation as a primary feature.
- `TODAY.md` is a query-shape-and-capability snapshot ("what GraphQL queries work in fakeshop today?"). The cooperation contract is not a query-shape change; the fakeshop schema is unchanged by this card.
- Same posture as [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] Slice 3 and [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] Slice 3.

This Decision never carried an `Alternatives considered (and rejected):` list.

### Changes this Decision underwent

None across the five revisions.

## Decision 9 — Joint `0.0.7` cut

Spec text: [Decision 9][spec-023-d9]. Contract that stays: `0.0.7` cards accumulate `### Added` entries under one shared heading, and the last card to ship owns the version bump.

### Justification (moved from the spec)

- Restates [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut] verbatim so this card's reader does not have to chase the cross-spec reference.
- Per [`KANBAN.md`][kanban] #"The last `0.0.7` card to ship owns the version bump": "The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-020-list_field-0_0_7.md`." The cross-card policy is already pinned in the [`KANBAN.md`][kanban]; this Decision pulls it into the spec so Slice 3's checklist can reference it.
- The [`CHANGELOG.md`][changelog] `[0.0.7]` `### Added` section already carries `DONE-020-0.0.7`'s [`DjangoListField`][glossary-djangolistfield], `DONE-021-0.0.7`'s [`Django AppConfig`][glossary-django-appconfig], and `DONE-022-0.0.7`'s [`Schema export management command`][glossary-schema-export-management-command] entries (verified at [`CHANGELOG.md`][changelog] #"## [0.0.7] - " under the `### Added` subsection); this card appends a fourth bullet for [`Multi-database cooperation`][glossary-multi-database-cooperation].

### Alternatives considered (and rejected)

- **This card bumps `0.0.7` because the cooperation contract is the natural release-cut sentinel.** Rejected: ship order is determined by which card a maintainer picks up next, not by topical fit; pinning the bump to a specific card creates a sequencing constraint that has no engineering justification.
- **Add a separate `TODO-ALPHA-XXX-0.0.7 — 0.0.7 release cut` card to [`KANBAN.md`][kanban] that owns the bump.** Rejected: out of scope for this spec (the spec's boundary forbids editing [`KANBAN.md`][kanban] outside the column move in Slice 3); the "last card to ship" policy is workable as-is.

### Changes this Decision underwent

- **rev4 V4** rewrote the [`KANBAN.md`][kanban] Done-body and [`CHANGELOG.md`][changelog] wording this Decision governs. rev2's counts ("four resolver-level tests … three optimizer-plan-level tests … and `_check_n1`") went stale the moment rev3 R2 moved the strictness test out of the optimizer file; both entries were re-pinned to five resolver-level plus two optimizer-plan-level, and the CHANGELOG's "/ strictness shape" leftover was dropped.

### Claims this Decision may no longer make

- That `DONE-025-0.0.7` is "still in flight". The whole `0.0.7` bundle shipped 2026-05-27 with seven cards, tag `0.0.7` at `72f6cd9`. Reconciling the spec sentence is Slice 2's.

## Deliberation moved from non-Decision sections

Every `revN Xn` attribution outside the nine Decisions is recorded above under the Decision it serves. The ones that do not map onto a Decision:

- **`## Slice checklist` / `## Edge cases and constraints`, rev2 S11.** rev1 claimed test docstrings were "required by `D102`". Verified false against `pyproject.toml #"[tool.ruff.lint.per-file-ignores]"`: `tests/**/*.py = ["D", "ANN", ...]`, so neither docstrings nor annotations are gate-forced in tests, and the missing-docstring code for a free function would be `D103` rather than `D102` in any case. The checklist bullets were rewritten to "convention-matching only" and to forbid `# noqa` suppressions for `D` / `ANN`, which is what the spec still says.
- **`docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`, rev2 S12.** rev1's CSV anchored `Meta.preferred_database` to the `multi-database-cooperation` heading as a workaround for having no heading of its own — mis-anchoring a hypothetical post-`1.0.0` key to a shipped behavior entry. The row was removed and the concept left as plain out-of-scope prose. The CSV's `notes` column carried two `rev2 H2` / `rev2 H6` attributions past this pass, which had no write access to it; Slice 2 de-attributed both, and `grep -o 'rev[0-9]'` over the CSV now returns 0.
- **`## Edge cases and constraints`, rev2 H3 and rev4 V1 (the `plan_optimizations` call shape).** rev1 told the implementer to "run a queryset through `plan_optimizations`", an API that does not exist; rev3's correction, `plan_optimizations(selections, model, parent_type)`, mis-positioned the third argument, which is `info` — the walker later calls `info.path`, so a class object bound there crashes at the first descent into the selection tree. rev4 V1 pinned the real signature and renamed `selections` to `selected_fields` throughout. The surviving spec sentence states the corrected shape and the `OptimizationPlan.apply` unit-of-test conclusion directly.
- **`## Test plan`, rev4 V2 and V3 (the strictness test's `kind=`).** rev2 / rev3 pinned `_check_n1(..., kind="many_to_one")`. Verified against `django_strawberry_framework/utils/relations.py #"RelationKind: TypeAlias"` that `"many_to_one"` is not a member; `_check_n1` accepts any string at runtime but `is_many_side_relation_kind("many_to_one")` is `False`, so the call fell through to `_will_lazy_load_single` and rev3's `_prefetched_objects_cache = {}` setup asserted nothing. rev4 V2 changed the kind to `"forward_single"`; rev4 V3 rewrote the setup to match the single-valued detector — `field_name` absent from `__dict__` and from `_state.fields_cache`, and no `_prefetched_objects_cache`.
- **`## Implementation plan`, rev4 V7.** A sweep item that confirmed the row-1 annotation already named the rev3 R2 strictness relocation and changed nothing.
- **`## Implementation plan`, rev2 line-delta adjustment.** The total expected delta was raised from ~330 to ~380 lines to reflect the split test files (H4), the live-HTTP fixture (H7), and the full-chain seeding (H9). The estimate survives in the spec; its revision history does not.

## Claims the spec may no longer make

Recorded here so a reader can see a claim was once asserted. Items 1-3 are retracted **by the spec's own later revisions**. Item 4 was still live in the spec when Slice 1 recorded it and was closed by Slice 2. All four are absent from the spec.

1. That the optimizer sets a queryset's `_db` before plan application (rev2 H1), that `Prefetch` chains generally respect routing (rev2 H2), and that strictness mode tracks the originating connection (rev2 H6). All three were rev1 claims verified false against source.
2. That the FK-id elision stub "inherits the routing context of the parent row" (rev3 R7). That describes what a consumer's router typically does with the `instance=` hint, not what the package contracts; the package forwards the hint and adopts whatever the router returns.
3. That test docstrings are required by `D102` (rev2 S11), and that `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` may anchor `Meta.preferred_database` to the cooperation entry (rev2 S12).
4. **A surviving letter drift of the rev5 X1 class.** [`## Risks and open questions`][spec-023-risks-and-open-questions] cited the strictness test as **(g)**; in the post-rev3-R2 numbering it is **(e)**. rev5 X1 fixed the same drift in [Decision 3][spec-023-d3] and X2 / X3 fixed two sibling bullets, but that occurrence was missed, and the same section's consumer-`Prefetch` bullet disagreed with `## Edge cases and constraints` on whether that test was (f) or (g). Slice 1 left every letter untouched — pre-correcting during a move is how a move becomes an unreviewable diff — and Slice 2 corrected three sites. The spec now has 0 occurrences of `(g)`, and its 40 `(a)`-`(f)` references all resolve to the six-test a-f layout.

## Slice 2 — spec reconciliation (what changed, and why the spec may now say it)

Slice 1 moved the deliberative layer out. Slice 2 made the surviving contract true at `HEAD`. Everything below is the record of that pass; none of it is in the spec.

### The reading this pass chose, and the one it rejected

Two defensible readings of what a shipped spec IS were open, and they decide the two largest corrections (the dead single-hit grep, and axis 3's plan-time-vs-fetch-time boundary).

- **Chosen — the spec is the durable record of the cooperation contract.** Its own `Status:` line says exactly that ("retained at this path as the durable record of the cooperation contract"), so a reader arriving at it should be able to act on what it says without knowing when it was written. Every factual claim about the package therefore describes `HEAD`, and cooperation behavior that landed later but sits inside the four axes' subject matter is absorbed into the spec body.
- **Rejected — the spec is a frozen record of what card `023` shipped**, with later call sites noted only here. It loses on two counts. First, it makes the file unusable as what its own header claims it is: a reader would have to reconstruct the current contract by diffing the spec against three years of cards. Second, it does not actually avoid the problem it is meant to avoid — a frozen spec still has to be read *as of* a date the file does not carry, which is the chronology the `docs/builder/BUILD.md` `## Spec rationale extraction` rule exists to forbid.

**The boundary the chosen reading does NOT cross.** A contract may state when a behavior arrived, the way [`docs/GLOSSARY.md`][glossary] does ("As of `0.0.10`, …"), because a consumer relies on that. What is banned is narrating the *spec's own* editorial history — "corrected from", "as of review round N", "this used to say". Concretely, the line this pass drew: a version, a release, or a card id appears in the spec only where the reader needs it to use the contract (the joint-cut policy, the card id in the header, the `0.0.7` target); no sentence in the spec says anything about a previous state of the spec. The `## Implementation plan` line-delta table is the one place forward-looking planning language survives, and deliberately — see the last subsection.

### Populations measured for this pass

Measured against the spec as Slice 1 left it, before any Slice 2 edit. Two of the three catalog figures this pass inherited were wrong, and re-deriving them is what caught it.

| Population | Catalog said | Measured | Instrument |
|---|---|---|---|
| broken `#decision-9--joint-0_0_7-cut` anchor uses in the spec | 2 | **7** | `grep -o '#decision-9--joint-0_0_7-cut' \| wc -l` |
| `test_query/` `.py` modules | "22 modules" | 21 test modules **+ `conftest.py`** = 22 files | `ls examples/fakeshop/test_query/*.py` |
| `tests/optimizer/` test modules | 17 | **15** (plus `__init__.py` and `_builders.py`) | `ls tests/optimizer/test_*.py \| wc -l` |
| package modules containing a code-level `.using(` call | "ten" | **9** modules (13 mention the token; `utils/querysets.py`, `optimizer/lateral_fetch.py`, `optimizer/nested_fetch.py`, `optimizer/nested_planner.py` mention it only in prose) | `grep -rn '\.using(' django_strawberry_framework/` read line by line |
| `router.db_for_read` / `db_for_write` **call** sites | 3 named | **4** (`types/resolvers.py`, `utils/permissions.py`, `utils/write_transaction.py` twice) | `grep -rn 'router\.db_for_' django_strawberry_framework/` minus docstring lines |
| `WIP-ALPHA-019-0.0.7` occurrences in the spec | not counted | 4 | `grep -o 'WIP-ALPHA-019-0.0.7' \| wc -l` |
| `rev[0-9]` attributions in the terms CSV | 2 | 2 | `grep -o 'rev[0-9]' \| wc -l` |

**The instrument lesson this pass repeats.** `grep -rn "\.using("` over a package answers "which files contain the token", not "which files call it". Four of the thirteen hits are docstrings and error-message strings describing the concept. A population defined as *call sites* has to be read line by line; the file list is a candidate set, not the answer.

### D1 — the dead single-hit grep

`## Current state` bullet 1 asserted that `_build_fk_id_stub`'s `router.db_for_read` is "the package's only explicit `router.db_for_read` call; verified by `grep -rn "router\|using\|_db\|db_for" django_strawberry_framework/` returning that single hit." That grep returns dozens of hits at `HEAD` and four genuine `router.db_for_*` call sites. Decision 2's justification carried the same claim in its own vocabulary; Slice 1 moved that half here with a time-scope warning, leaving the two halves split across files — the split this slice closes.

**What the spec now says.** The elision-stub call is described as what it actually is: the **read**-path router consultation the four axes cover, and the only one in the optimizer / type layer. The other three are named with their symbol-qualified paths and placed outside the axes, because they are: the permission layer's candidate-alias collection is authorization, and the two write-alias resolutions belong to the write pipeline. The scope statement survives; the grep that could once prove it does not, so it is gone rather than restated with a longer pattern — a grep quoted in a spec is a claim with an expiry date.

### D2 — axis 3 is alias-LATE, not alias-absent

The verified facts, all still true at `HEAD`:

- Plan construction does not route. `optimizer/walker.py::_build_child_queryset` still starts from `field.related_model._default_manager.all()` and applies only `target_type.get_queryset(qs, info)`.
- Fetch time does route. `optimizer/single_parent_fetch.py #"child_qs = spec.pristine_child_queryset.using(queryset.db)"` pins the degenerate single-parent child to the parent's alias; `filters/sets.py #"child_manager.using(parent_db).all()"` pins a related filter's child base so an alias-sensitive `get_queryset` hook runs on the parent's shard; and `optimizer/nested_planner.py #"correct alias-late predicate at fetch time"` records why the planner deliberately refuses to resolve a generic relation's content type early — an unrouted child queryset asks the router without the parent-instance hint, and a cached plan would preserve the wrong constant.

So the spec's flat "generated `Prefetch` child querysets do NOT inherit the root alias" was never wrong about the plan and was always incomplete about the fetch. **The reconciled statement makes the plan/fetch boundary explicit at all seven sites** — `## Key glossary references`, `## Problem statement`, `## Goals` item 1(c), `## User-facing API`, `### Decision 3` axis 3, `## Edge cases and constraints`, `## Risks and open questions` — and `## Out of scope` now defers shard-aware *planning* (an alias resolved at plan-construction time) rather than "threading the parent `_db` into generated child querysets", which is a thing the package does.

**Consistency with the shipped GLOSSARY was a hard constraint, not a preference.** [`docs/GLOSSARY.md`][glossary]'s `## Multi-database cooperation` entry is the shipped four-axis statement and is outside this cycle's writable set. Its axis 3 reads "generated `Prefetch` child querysets do NOT inherit the root alias" with no qualifier. That sentence is about the *plan*, which is what the entry is describing, and the shipped [`CHANGELOG.md`][changelog] bullet for this card already spells the qualifier out ("do NOT inherit the root alias **at plan-construction time**"). The spec's expanded wording is therefore a refinement of the GLOSSARY line, never a contradiction of it, and the CHANGELOG is the precedent for the exact phrase.

**Rejected alternative:** add a fifth axis. It would put the spec out of step with the shipped GLOSSARY entry and the shipped CHANGELOG bullet, both of which say "four axes", and both of which this cycle may not edit. The alias-late behavior is not a fifth promise anyway — it is how axis 3's promise is kept.

### D6 — the resolver-level alias re-pin, added without a fifth axis

`types/resolvers.py::_visible_related_object` #"source = source.using(alias)" reads a related row's own `_state.db` and pins the visibility re-check queryset to it, so a `shard_b` row's `get_queryset` predicate is evaluated on `shard_b`. That is cooperation behavior squarely inside this contract's subject matter and appeared nowhere in the spec.

It is now stated twice: as a contract sentence in `## User-facing API`'s `get_queryset` bullet, and as the closing paragraph of `### Decision 3` — framed as the clearest instance of the same alias-late principle axis 3 describes, immediately before the out-of-scope list, so a reader cannot mistake it for a fifth axis. Same reason as above: "four axes" is load-bearing across three shipped surfaces.

### D7 — the heading rename, and why a Decision was allowed to change its own name

`### Decision 7` was titled *Reuse the `test_library_api` reload fixture verbatim* and its contract sentence said the module copies the autouse fixture verbatim from `test_library_api.py`. **Both are false at `HEAD`.** `examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests` is the tree's single module-scoped autouse definition, no module carries a private copy, and `test_multi_db.py` reaches it by depending on it from `_build_test_schema`.

This was not a claim that rotted by accident. The Decision's own justification named the condition that would justify extraction — "a `conftest.py` shared across `test_query/` files, justified once 2+ files need it" — and set the boundary as "do not pre-emptively factor". The condition was met and the extraction happened. The Decision's escape clause fired, so the spec states the shipped source of the fixture and the heading names the settled question rather than the superseded answer.

**Cost of the rename, paid in the same pass:** the anchor `#decision-7--reuse-the-test_library_api-reload-fixture-verbatim` had 8 uses in the spec and 7 in this file; all 15 were rewritten to `#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest`, and this file's own heading moved with them. Three dependent spec sentences (`## Slice checklist`, `## Current state`, `### Decision 6`'s pattern bullet, `## Test plan`'s existing-tests note, `## Definition of done` item 3) were rewritten to match, and `### Decision 6`'s pinned module header dropped its `importlib` / `sys` imports — they existed only to support a locally-copied reload fixture that no longer exists, and the shipped file does not import them.

**Rejected alternative:** keep the heading and rewrite only the body. A heading that contradicts its own body is worse than a stale heading, and the anchor would then advertise the retracted answer to every cross-reference.

### D14 — the broken anchor was 7 uses, not 2

`### Decision 9 — Joint `0.0.7` cut` slugs to `decision-9--joint-007-cut`: a dotted version's dots are stripped, so `0.0.7` becomes `007`, not `0_0_7`. Slice 1 reported two uses of the wrong spelling. There were **seven** — the `Predecessors:` line, two `## Slice checklist` bullets, two `## Doc updates` bullets, one `## Risks and open questions` bullet, and `## Definition of done` item 15. All seven now resolve.

Two further broken in-page anchors nobody had reported turned up in the same sweep: `## Doc updates`' GLOSSARY pin quoted the entry body's own `](#djangooptimizerextension)` and `](#optimizerhint)` links verbatim. Those resolve inside `docs/GLOSSARY.md` and nowhere else, so from the spec they were dead. They now use the spec's existing `[glossary-djangooptimizerextension]` / `[glossary-optimizerhint]` reference ids: the pinned *text* is unchanged, only the target is re-relativized to where the sentence actually lives — which is the whole point of `START.md`'s reference-style convention.

**Instrument note for the next pass.** Slice 1's verification reported "in-page anchors, both files: all resolve, with one pre-existing exception". It found the exception it was told about and did not enumerate the population. A resolver that walks every `](#…)` against the file's own computed heading slugs found three distinct broken targets across 9 occurrences in about a second. Verify anchors with a resolver, never by checking the one you already know about.

### D19 / D20 — the pinned doc wording versus what shipped

- **GLOSSARY:** the shipped entry body matches the spec's pin word for word. No change beyond the two re-relativized anchors above.
- **`docs/README.md`:** the shipped `### Sharded mode (multi-DB)` prose and the forward-pointer sentence both match the pin word for word. No change.
- **CHANGELOG:** the shipped bullet diverges from the pin in one phrase — the spec quoted `AGENTS.md #"Test through real usage, prefer the example project"` where the shipped bullet says "per the repository's real-query coverage rule". The pin now matches what shipped. Two further divergences were **deliberately not mirrored**: the shipped bullet's own reference ids (`[optimizer-multi-db]`, `[fakeshop-multi-db]`, `[db-shard-b]`) are `CHANGELOG.md`-local and would not resolve from the spec, and its trailing "Tracked as [019-multi_database_cooperation_contract-0.0.7] …" sentence carries a pre-renumber card label that [`KANBAN.md`][kanban] itself documents as a known-stale surface owned by another card. Importing either into the spec would import a defect.
- **KANBAN:** the spec pinned a long free-prose Done body. **That shape was never renderable.** `KANBAN.md` is generated from the kanban DB, so every card comes out as fixed metadata rows plus a `#### Glossary terms` table, `#### Verified in upstream` bullets, and a `#### Note`. The pin has been rewritten to state the card's four actual obligations against that structure. `## Slice checklist` and `## Definition of done` item 13 were rewritten to match.

### D18 — the card id

`WIP-ALPHA-019-0.0.7` appeared 4 times (`## Slice checklist`, two `## Doc updates` bullets, `## Definition of done` item 13). The card is `DONE-023-0.0.7`; the WIP id is a state the board no longer has, and "moved from `WIP-ALPHA-019-0.0.7` in Slice 3" is precisely the chronology a reader would have to apply. All four are gone; 0 occurrences remain.

### D11 — the archive already happened

`### Decision 1` still described the spec as the active in-flight document at `docs/spec-023-multi_db-0_0_7.md` and reasoned about what a *future* archive pass would do. The archive has run. The Decision now states where the file and its two companions are, and keeps the path-lifecycle rule as a general rule (an in-flight spec is at `docs/spec-…`; Step 8 moves it and its companions) rather than as a prediction about this one. `## Goals` item 1 and `## Definition of done` item 1 were re-pointed at the archived paths, the CSV's included.

### D16 (found this pass) — the fakeshop `default` alias is no longer unconditional

`## Current state` said `default → db.sqlite3` "is declared unconditionally in both single-DB and sharded modes". At `HEAD` two env vars re-point it: `DJANGO_STRAWBERRY_KANBAN_DB` swaps the SQLite file so the doc-render tooling can run against a migrated copy of the board DB, and `FAKESHOP_PG_DSN` swaps the whole `default` entry to Postgres for the vendor tier (mutually exclusive with `FAKESHOP_SHARDED`). The additive property the contract actually rests on — sharded mode ADDS `shard_b` and never replaces `default` — is untouched by either, so the bullet now states the additive property and names the two overrides instead of asserting one fixed file. `DATABASE_ROUTERS` is still absent from the settings module; that bullet was re-verified and left alone.

### Claims corrected without a catalog entry

- **`plan_optimizations`'s pinned signature** gained the keyword-only `runtime_prefixes` (`optimizer/walker.py::plan_optimizations`). The spec's conclusion — the third positional is `info`, there is no `parent_type` positional, `OptimizationPlan.apply` is the right unit of test — is untouched.
- **`_build_fk_id_stub`'s pre-router exits** are now three, not one: absent `attname` / `related_model`, the `_FK_ELISION_UNSAFE` return when the FK column is deferred on `root`, and the null-FK `return None`. The `## Edge cases and constraints` bullet said the router call "only runs when `related_id is not None`", which is true but no longer the whole guard. Naming all three is what keeps a reader from adding a fourth in the wrong place.
- **`## Current state`'s enumerated `tests/optimizer/` inventory is gone.** It listed seven module filenames; there are 15. Replacing seven names with fifteen would re-rot on the next card, so the bullet now states the durable structural fact (the directory is an established test package, so `test_multi_db.py` extends it in place and needs no new subdirectory) and enumerates nothing.
- **The version-pin bullet no longer quotes `0.0.6`.** It names the three files that move together and states that none of them is this card's to touch, which is the contract; the numbers themselves belong to whichever release is current.
- **`## Risks and open questions` bullet 1** asserted `## [0.0.7] - 2026-05-20` and that the three version pins "all still pin `0.0.6`". The heading reads `## [0.0.7] - 2026-05-27` and the package is at `0.0.14`. The bullet now states the standing hazard of the joint-cut policy — a shared `[0.0.7]` heading accumulates entries before any card bumps the version — without quoting a date or a version. Its fallback ("if the maintainer decides `0.0.7` is in fact released and this card should target `0.0.8`, the spec filename moves to `docs/spec-019-multi_db-0_0_8.md`") was **deleted rather than moved**, per [`worker-1.md`][worker-1] rule 2: the contingency did not fire, the card shipped in `0.0.7`, and the filename it names never existed.
- **`### Decision 9`** described `DONE-025-0.0.7` as "still in flight" and the bundle as two cards. The `0.0.7` cut shipped 2026-05-27 with seven cards, tag `0.0.7` at `72f6cd9`. The Decision now states the policy — every card in the bundle appends under one heading, the bundle is cut once as a whole — with no roster and no status, because a roster is what went stale.
- **The live-test module's exhaustive readings.** `## Slice checklist`, `## Goals` item 3, `## Test plan`, `## Definition of done` item 3, and `### Decision 6`'s import annotation all read as though `examples/fakeshop/test_query/test_multi_db.py` were exactly these two tests importing exactly `DjangoOptimizerExtension`. It holds ten. Each site now says what this contract contributes to the module rather than what the module contains, and the import annotation pins what these two tests need rather than a ceiling on the file.
- **The terms CSV.** Two `notes` cells carried `rev2 H2` / `rev2 H6` round attributions; both now describe the term's role in the contract. Three more cells named sibling cards by their pre-renumber ids (`DONE-016` / `DONE-017` / `DONE-018`) and now read `DONE-020-0.0.7` / `DONE-021-0.0.7` / `DONE-022-0.0.7`; the `Multi-database cooperation` row's note described the status flip rather than the term. One row per anchor throughout — the grammar `import_spec_terms` requires — verified by `awk -F',' 'NR>1{print $2}' | sort | uniq -d` returning empty over all 18 rows.

### Time-scope note on this file's own `## Revision history`

`## Revision history` is a verbatim record of what five review rounds said, so its statements are true *of those rounds* and are not descriptions of `HEAD`. Two are worth flagging because a later reader could mistake them for current:

1. **rev4 V2** quotes `RelationKind` as the four-member `Literal["many", "reverse_many_to_one", "reverse_one_to_one", "forward_single"]` and `MANY_SIDE_RELATION_KINDS` as `{"many", "reverse_many_to_one"}`. At `HEAD` both carry a fifth / third member, `"generic"` (`utils/relations.py #"RelationKind: TypeAlias"`, `#"MANY_SIDE_RELATION_KINDS"`). The round's *conclusion* is unaffected: `"forward_single"` is still the right kind for a forward FK and `"many_to_one"` is still not a member. **No spec edit was needed** — the quoted membership only ever lived in the revision history Slice 1 moved here, and `grep -c 'reverse_one_to_one\|MANY_SIDE_RELATION_KINDS' docs/SPECS/spec-023-multi_db-0_0_7.md` returns 0. This is the build plan's D4, closed as already-discharged rather than as a spec change.
2. **rev2 H3** states the `plan_optimizations` signature as "selections + model + parent_type" and **rev4 V1** corrects it to `plan_optimizations(selected_fields, model, info=None, *, source_type=None)`. `HEAD` adds keyword-only `runtime_prefixes`. The spec's live sentence carries the full current signature; the history keeps rev4's.

### Deliberately not changed

- **`## Implementation plan`'s line-delta table.** Its `+180 / -0`, `+160 / -0`, `+22 / -6`, "~380 lines" are a planning estimate and the section is the plan record, so the numbers are not claims about `HEAD` and rewriting them to shipped figures would state something the file never meant. The shipped delta is not measurable as one figure in any case: the card landed across several commits (the largest, `3bc2330b`, mixes it with two siblings' artifacts) and all three files have since been rewritten by later cards. Checked, and left.
- **`## Borrowing posture`'s upstream paths.** `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py` and the `python3.14` `graphene_django` site-packages path both still exist on this machine, and [`KANBAN.md`][kanban]'s own `#### Verified in upstream` bullets restate the same finding. Left as written.
- **Every `- [ ]` checkbox.** The `Status:` line is the source of truth for a shipped card; unticked boxes in an archived spec are the house convention and are not a claim.
- **`## Risks and open questions` as a section.** Slice 1's judgement call to keep it stands: preferred-answer-plus-fallback is forward-looking contingency, not chronology. Two bullets whose contingency has since resolved were rewritten in place (above); the section stays.

### Verification performed by this pass

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-023-multi_db-0_0_7.md` -> `OK: 18 terms - all have glossary entries and at least one spec link.` exit 0. Unchanged from Slice 1's close; the three joint-cut glossary terms kept their `## Doc updates` link site through the CHANGELOG-pin rewrite, which is where that rewrite could have dropped them.
- `uv run python scripts/check_trailing_commas.py --check` on the spec, this file, and the terms CSV -> exit 0.
- In-page anchors, both files: every `](#…)` resolved against the file's own computed heading slugs. 0 unresolved, from 3 distinct broken targets before the pass.
- Reference ids, both files: `used-not-defined: []`, `defined-not-used: []` (code spans and fenced blocks stripped first). One def, `[test-library-api]`, was orphaned by the Decision 7 rewrite and removed from the spec; it is still used here.
- Every link-definition path in both files disk-exists-checked, and every cross-file `#fragment` resolved against the target file's real headings. 0 failures — this is what caught `[rationale-d7]` pointing at the pre-rename anchor.
- No `pytest`, no `--cov*` flag, no source or test file touched, no commit, no branch.

## Verified against the shipped code

- **The code shipped the spec exactly.** Worker 0's pre-dispatch verification read every Definition-of-done item against `HEAD` before this cycle was dispatched: all six package-internal tests and both live `/graphql/` tests exist under the spec-pinned names, the Slice 3 doc edits all landed, and the four contract axes still hold in source. Nothing was skipped at build time — which is why this cycle changes no code and no tests. The evidence table is in `docs/builder/build-023-multi_db-0_0_7.md` `## Pre-dispatch verification`.
- **Every count stated above was measured at the time of writing**, with the instrument named alongside it.
- **The two byte figures were measured after the last edit either file received** and re-measured whenever one of them moved.
- **The post-move sweep returned zero.** `grep -cE 'rev[0-9]' docs/SPECS/spec-023-multi_db-0_0_7.md` reports 0, `scripts/check_spec_glossary.py` still exits 0 at 18 terms, and every reference-style id used in the spec body still resolves to a definition.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[backlog]: ../../../BACKLOG.md
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md
[pyproject]: ../../../pyproject.toml

<!-- docs/ -->
[glossary-django-appconfig]: ../../GLOSSARY.md#django-appconfig
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-metaoptimizer-hints]: ../../GLOSSARY.md#metaoptimizer_hints
[glossary-multi-database-cooperation]: ../../GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: ../../GLOSSARY.md#optimizerhint
[glossary-schema-export-management-command]: ../../GLOSSARY.md#schema-export-management-command
[glossary]: ../../GLOSSARY.md
[readme]: ../../README.md
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next-step-8--archive-prior-specs-and-update-cross-references]: ../NEXT.md#step-8--archive-prior-specs-and-update-cross-references
[next]: ../NEXT.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md
[spec-020-decision-10--joint-007-cut]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-022]: ../spec-022-export_schema-0_0_7.md
[spec-023-current-state]: ../spec-023-multi_db-0_0_7.md#current-state
[spec-023-d1]: ../spec-023-multi_db-0_0_7.md#decision-1--spec-filename-and-canonical-naming
[spec-023-d2]: ../spec-023-multi_db-0_0_7.md#decision-2--no-production-code-change
[spec-023-d3]: ../spec-023-multi_db-0_0_7.md#decision-3--the-cooperation-contract-four-axes
[spec-023-d4]: ../spec-023-multi_db-0_0_7.md#decision-4--no-routing-decoration-on-fakeshop-schemas
[spec-023-d5]: ../spec-023-multi_db-0_0_7.md#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded
[spec-023-d6]: ../spec-023-multi_db-0_0_7.md#decision-6--live-coverage-under-fakeshop_sharded1
[spec-023-d7]: ../spec-023-multi_db-0_0_7.md#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest
[spec-023-d8]: ../spec-023-multi_db-0_0_7.md#decision-8--no-readme--goal--today-edits
[spec-023-d9]: ../spec-023-multi_db-0_0_7.md#decision-9--joint-007-cut
[spec-023-definition-of-done]: ../spec-023-multi_db-0_0_7.md#definition-of-done
[spec-023-doc-updates]: ../spec-023-multi_db-0_0_7.md#doc-updates
[spec-023-edge-cases-and-constraints]: ../spec-023-multi_db-0_0_7.md#edge-cases-and-constraints
[spec-023-goals]: ../spec-023-multi_db-0_0_7.md#goals
[spec-023-implementation-plan]: ../spec-023-multi_db-0_0_7.md#implementation-plan
[spec-023-key-glossary-references]: ../spec-023-multi_db-0_0_7.md#key-glossary-references
[spec-023-problem-statement]: ../spec-023-multi_db-0_0_7.md#problem-statement
[spec-023-risks-and-open-questions]: ../spec-023-multi_db-0_0_7.md#risks-and-open-questions
[spec-023-slice-checklist]: ../spec-023-multi_db-0_0_7.md#slice-checklist
[spec-023-terms]: spec-023-multi_db-0_0_7-terms.csv
[spec-023-test-plan]: ../spec-023-multi_db-0_0_7.md#test-plan
[spec-023-user-facing-api]: ../spec-023-multi_db-0_0_7.md#user-facing-api
[spec-023]: ../spec-023-multi_db-0_0_7.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->
[field-meta]: ../../../django_strawberry_framework/optimizer/field_meta.py
[plans]: ../../../django_strawberry_framework/optimizer/plans.py
[relations]: ../../../django_strawberry_framework/utils/relations.py
[resolvers]: ../../../django_strawberry_framework/types/resolvers.py
[walker]: ../../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-plans]: ../../../tests/optimizer/test_plans.py
[test-walker]: ../../../tests/optimizer/test_walker.py

<!-- examples/ -->
[models]: ../../../examples/fakeshop/apps/library/models.py
[test-library-api]: ../../../examples/fakeshop/test_query/test_library_api.py
[test-query-conftest]: ../../../examples/fakeshop/test_query/conftest.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
