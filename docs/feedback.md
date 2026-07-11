# Spec-044 implementation review — `DjangoDebugExtension` (commit `cd82627a`)

Reviewed: the full 10-file diff of `cd82627a` ("Finish spec-044-debug_extension-0_0_14.md")
against `docs/spec-044-debug_extension-0_0_14.md` (Revision 8) and `AGENTS.md`, with every
load-bearing engine claim re-verified against the installed `strawberry-graphql==0.316.0`,
Django, and repo sources. Per the AGENTS.md workflow rule ("Do not run pytest after edits;
run only when explicitly asked") **no test suite was executed for this review** — everything
below is source-level verification; the run-level gates (full suite, `fail_under = 100`,
the sharded tier, the floor node) remain yours to execute.

## Verdict

Slice 1 is a faithful, decision-complete implementation of the Revision-8 spec — every
Slice-1 row of the Implementation plan landed, every Test-plan scenario (1–21) has an
implemented owner in the correct tier, the DRY obligations (D1–D6, D-N1–D-N8) are honored
to the letter, and all mechanical gates I can run without pytest pass. **One P0 defect
ships in the diff: the new CI Strawberry-floor step calls `strawberry.__version__`, which
does not exist in 0.316.0, so the minimum-support CI nodes fail deterministically on every
push/PR.** Beyond that: the commit message overstates ("Finish") — Slices 2 and 3 are
still open by the spec's own plan — plus a short list of minor polish items.

---

## F1 (P0) — CI floor-verification step crashes: `strawberry.__version__` does not exist

`.github/workflows/django.yml`, the new "Install Strawberry (minimum supported floor)"
step ends with:

```
uv run --no-sync python -c "import strawberry; print('strawberry-graphql', strawberry.__version__)"
```

Verified against the installed 0.316.0 (the exact version the step force-installs):
`strawberry` exposes **no `__version__` attribute** — `hasattr(strawberry, "__version__")`
is `False`, `dir()` has no version-shaped name, and `strawberry/__init__.py` defines
nothing of the sort (no lazy `__getattr__` fallback either; `hasattr` would have
triggered it). The line raises `AttributeError`, the step exits non-zero, and **every
push/PR fails on the minimum-support node** (plus both dispatch-tier min nodes). The
spec's requirement — "recording the resolved version makes the exercised floor auditable
in the log" — is exactly the half that's broken; the
`uv pip install "strawberry-graphql==0.316.0"` half is fine.

Root-cause fix (AGENTS.md #"highest standard" — not `|| true`, not deleting the audit
line): read the distribution version, which is the thing actually being pinned:

```
uv run --no-sync python -c "import importlib.metadata as m; print('strawberry-graphql', m.version('strawberry-graphql'))"
```

Until this lands, the DoD's "the floor is durably exercised by a CI node" item is not
met — the node exists but can never go green.

## F2 (P1) — "Finish spec-044" overstates: Slices 2 and 3 are open, and correctly so

What landed is exactly the spec's **Slice-1** file map (all ten rows present and
verified: `extensions/__init__.py`, `extensions/debug.py`, both test modules,
`tests/extensions/__init__.py`, the pyproject/uv.lock floor raise, the workflow node, the
`optimizer/extension.py::DjangoOptimizerExtension.__init__` comment correction, and the
scenario-16 addition to `test_multi_db.py`). Still open, per the spec's own Slice
checklist and confirmed by the live `TODO(spec-044 Slice N)` anchors:

- **Slice 2** — GLOSSARY entry body via the glossary **DB + re-render** (never a
  hand-edit), `docs/TREE.md` regen after the `TrackedPath.is_current` flips, the
  `examples/fakeshop/apps/kanban/constants.py` tracked-path registrations, the
  `config/schema.py` stale "no direct Strawberry analogue" docstring rewrite (its
  `TODO(spec-044 Slice 2)` anchor is still live and is now *actionable* — the sentence it
  guards is now false), and the `GOAL.md` criterion-7 scoping sentence.
- **Slice 3** — the version quintet (anchors in place at `pyproject.toml`,
  `django_strawberry_framework/__init__.py`, `tests/base/test_init.py::test_version`;
  package version correctly still `0.0.13` everywhere including uv.lock), the GLOSSARY
  status flips from the companion `docs/spec-044-debug_extension-0_0_14-terms.csv`,
  README / docs/README / TODAY wording, CHANGELOG under the Slice-3 grant, and the
  ordered DB-mutations-first → Done flip → `import_spec_terms` → renders → `--check`
  card wrap. The card is correctly still `WIP-ALPHA-044-0.0.14` in KANBAN.md.

None of this is a defect — the staging follows AGENTS.md #design-docs-and-TODO-anchors
exactly (Slice-1 anchors were removed in the shipping change; Slice-2/3 anchors remain).
The finding is only that "Finish" reads as spec-complete when it is Slice-1-complete;
the release is not cut and the docs surface still describes the extension as absent.

## F3 (P2) — DoD's isolated-floor run: command recorded, outcome not

The DoD requires the concurrent sync isolation scenario to pass "at that exact floor in
an isolated throwaway venv … the command/outcome are recorded". The command is recorded
twice (the node-id block in `tests/extensions/test_debug.py` above
`test_concurrent_sync_operations_use_isolated_instances`, and the spec Test plan), but I
find no recorded **outcome** in the repo. Mitigating: `uv.lock` currently resolves
`strawberry-graphql` to exactly `0.316.0`, so the ordinary full-suite run *is* a floor
run today, and once F1 is fixed CI exercises it durably. Suggest recording the isolated
run's outcome (or noting where it was recorded) when you run the suite.

---

## Verified sound — the engine and repo claims the design stands on

Each of these was checked against sources for this review, not taken from the spec:

- **Per-operation instantiation at the floor.** Installed 0.316.0
  `Schema.get_extensions` instantiates class/factory entries with **zero arguments** per
  operation, passes deprecated pre-built instances through as-is (warning at
  `Schema.__init__`), and no `_sync_extensions` cache exists anywhere in `schema.py`.
  `SchemaExtension.__init__(self, *, execution_context=None)` — so both the engine's
  `ext()` call and the tests' bare `DjangoDebugExtension()` are valid, and the corrected
  `optimizer/extension.py` comment ("Strawberry itself never passes this keyword" at the
  floor) is accurate.
- **One sync generator hook, both colors.** `strawberry/extensions/context.py` handles
  `isgeneratorfunction` and `isasyncgenfunction` hooks on both execution paths —
  Decision 7's single-generator shape is supported.
- **Scenario 7's envelope assertion.** `strawberry.http.process_result` includes
  `"extensions"` only when truthy; `DjangoOptimizerExtension` defines no `get_results`
  (base returns `{}`), so `set(res.response.json()) == {"data"}` is sound.
- **Coverage plumbing.** `[tool.coverage.report].exclude_lines` **replaces** coverage
  defaults, so the `# pragma: no cover` on the `TYPE_CHECKING` import is required, and it
  guards a genuinely unreachable line (AGENTS.md #pragma rule satisfied). My static walk
  maps every executable line of `debug.py` to a named owner test (both serializers, both
  collector guards, all four coordinator transitions, the clamp/rollover, both
  `get_results` directions, the pre-yield unwind, both degrade catches) — the 100% gate
  looks satisfiable, subject to the actual run.
- **Test-plan conformance, 1–21 complete.** Scenarios 1–7 live in
  `test_debug_extension_api.py` over real probe-URLconf HTTP; 8–15 and 17–21 in
  `tests/extensions/test_debug.py`; 16 in `test_multi_db.py` behind `FAKESHOP_SHARDED=1`.
  Markers match the plan exactly (1–2 `django_db`, 3 and 19 `transaction=True`,
  DB-touching mechanics marked, attribute-only tests unmarked). The Revision-8 additions
  are all present: the two-phase degrade (17), both cursor-boundary directions (18),
  transaction inclusion/exclusion (19), sibling-hook ordering in both list orders (20),
  and the hop policy incl. the 64-hop ceiling asserted as an independent literal (21).
  Scenario 13 correctly proves *instance* isolation (distinct thread-local wrappers, no
  ORM in executor threads) and defers same-wrapper refcounting to scenario 9, as
  respecified.
- **Fixture/precedent fidelity.** `seed_data` category privacy alternates by sorted
  index (deterministic), so `Category.objects.filter(is_private=False)…first()` can
  never return `None` — the deterministic post-seed `Item.objects.create` rows follow
  the established `test_products_api.py` precedent (AGENTS.md #seed-first satisfied:
  seeds are the first domain-setup action; scenario 3's `create_users(1)` →
  `seed_data(1)` ordering is DRY D3's sanctioned auth-first shape). The
  `GlobalID(type_name="products.category")` spelling matches `test_client_api.py`; the
  permitted-writer build (non-staff `view_item_1`, single `add_item` grant, re-fetch)
  matches its precedent; `categoryId` is required because `Item.category` is a non-null
  FK — all as respecified in Revision 8.
- **Scenario 2's two-query assertion** matches the shipped visibility contract (the
  `CategoryType.get_queryset` hook forces the `Prefetch` downgrade) and the precedent
  proof pins the same shape, including no COUNT — the "exactly 2 SELECTs" pin is sound.
- **DRY D1–D6 / D-N1–D-N8 all honored.** Module-level serializers with the six wire keys
  as literals and `isSlow`/`isSelect` derived inside; the explicit three-argument
  `traceback.format_exception` (post-`except` ambient state is gone — correct and
  documented); one `None`-guarded collector owning order-preservation and no-dedup; the
  two-seam lock-protected coordinator keyed by **wrapper object identity**, the only
  toucher of the flag; immutable snapshot records read back at serialization (never a
  second `connections.all()`); one log-slice helper owning the clamp; one payload builder
  owning the shape with fresh containers; **no `__init__`**; the 64-hop ceiling
  re-spelled locally with the extraction deferral recorded — precisely D6's instruction;
  zero `utils/` imports; nothing raised (D-N7). The `extensions/__init__.py`
  eager-export shape mirrors `utils`/`testing`.
- **Two-phase failure policy** implemented as the Error-shapes section specifies:
  pre-yield fail-loud with `ExitStack` unwind (pinned by the one sanctioned fake at the
  private acquisition boundary — never a runner mock), post-execution catches
  `Exception` (never `BaseException`), logs through the package logger, degrades the
  payload, never touches the result; flag restoration rides `ExitStack.callback` inside
  the `with`, separately protected from the diagnostic catch. The stash-absent
  `get_results() == {}` no-key contract and the real-engine conditional double call are
  both pinned by tests against real Strawberry execution.
- **Mechanical gates** (all run for this review, read-only): `uv run ruff format
  --check .` clean, `uv run ruff check .` clean, `check_trailing_commas.py --check`
  clean, all six changed/new `.py` files ASCII-only, no `path:NN` references in code or
  spec, no leftover `TODO(spec-044 Slice 1)` anchors, no orphan imports of the deleted
  planning-stub guard (the F21 deletion happened, correctly paired with the
  already-standing `raise NotImplementedError` coverage exclusion). `-n auto --dist
  loadscope` keeps each module's tests in one worker, so the shared-`queries_log`
  manipulation in the degrade test and the module-level probe holder are xdist-safe.

## Minor observations (polish; none block)

- **M1 — stale section label in `tests/extensions/test_debug.py`.** The coordinator
  block header reads "Scenarios 4-7 of the mechanics anchors" — numbering from the
  deleted TODO-anchor pseudocode, which no longer exists anywhere. Those tests are spec
  **scenario 8**'s components (restore contract / distinct wrappers / partial unwind /
  log slicing). Every other section header uses spec Test-plan numbers; this one should
  too, or a future reader will hunt for scenarios 4–7 in the wrong tier.
- **M2 — scenario 16's URLconf plumbing** uses the per-test
  `override_settings(ROOT_URLCONF=…)`/`clear_url_caches()` block, copying
  `test_multi_db.py`'s own established boilerplate rather than the new module's
  `pytest.mark.urls` idiom. DRY D3 explicitly scopes the single-siting rule to the new
  module and names this module's repetition as the precedent, so this is in-spec —
  worth a cleanup card only if that module grows again.
- **M3 — CI comment drift-in-waiting.** "The other nodes run the uv.lock-resolved
  (latest compatible) strawberry-graphql" — the lock currently resolves to exactly
  `0.316.0`, so floor and latest coincide until a newer strawberry is released and the
  lock re-resolved. Fine; just don't read the matrix as currently proving a version
  spread.
- **M4 — `test_off_by_default_publishes_no_debug_key`** is the only live scenario whose
  strongest assertion (`{"data"}` envelope) depends on *every* configured extension
  returning empty results; if a future extension ever publishes always-on results the
  test fails loudly and correctly, but the failure will point here rather than at the
  new extension. The docstring's "honest claim" framing covers it; nothing to change.

## AGENTS.md compliance ledger

- **#3 DRF-first**: no consumer decorator surface; the opt-in is engine `extensions=`
  configuration, with the GOAL.md criterion-7 scoping deferred to Slice 2 as planned. ✓
- **#4 highest standard**: Django-native debug cursor over a cursor-wrap port, fail-loud
  setup, spec'd degrade policy; F1's fix must stay root-cause (importlib.metadata). ✓/⚠ F1
- **#5/#6 placement**: package code in `django_strawberry_framework/extensions/`;
  mechanics in `tests/extensions/` (package with `__init__.py`, no helper exports); live
  HTTP in `examples/fakeshop/test_query/`; sharded proof gated in `test_multi_db.py`. ✓
- **#7 seed-first / no hand-rolled rows**: `create_users`/`seed_data` open every
  catalog/auth test; the two deterministic post-seed `Item.objects.create` rows follow
  the `test_products_api.py` precedent. ✓
- **#9 live-first**: everything request-reachable is earned over live `/graphql/`
  (scenarios 1–7); the package tier holds only request-impossible mechanics per
  Decision 11; serializer units are pure-function tests, the sanctioned coexistence. ✓
- **#10–#12 coverage**: source unchanged; the one new pragma is genuinely unreachable;
  gate confirmation requires the run (see commands below). ✓ (pending run)
- **#13**: tests in the same change; orphan sweep clean after the stub-guard removal. ✓
- **#14**: no pytest run in this review, per rule. ✓
- **#15–#17**: ruff format/check and the trailing-comma checker pass post-commit. ✓
- **#20**: no settings key added (the extension has no configuration). ✓
- **#21**: CHANGELOG untouched; the Slice-3 grant is not yet exercised. ✓
- **#26 TODO anchors**: Slice-1 anchors removed in the shipping change; Slice-2/3
  anchors staged at their seams. ✓
- **#27 references**: symbol-qualified refs throughout; no raw line numbers in code or
  the spec. ✓
- **#31 version**: `0.0.13` everywhere, quintet TODOs in place for Slice 3. ✓
- **#32/#33**: nothing committed or branched by this review; feedback only. ✓

## Commands for the maintainer (recorded, not run)

- Full gate: `uv run pytest`
- Targeted: `uv run pytest -o addopts="-v -n0" tests/extensions/test_debug.py`
  and `uv run pytest -o addopts="-v -n0" examples/fakeshop/test_query/test_debug_extension_api.py`
- Sharded scenario 16: `FAKESHOP_SHARDED=1 uv run pytest -o addopts="-v -n0" examples/fakeshop/test_query/test_multi_db.py`
- Floor isolation (isolated venv, per DoD):
  `uv run pytest -o addopts="-v -n0" "tests/extensions/test_debug.py::test_concurrent_sync_operations_use_isolated_instances"`

## Bottom line

Fix F1 before the next push (one-line CI change), then run the suite. With CI green,
Slice 1 is done to spec and the remaining work is the Slice-2 doc pass and the Slice-3
joint cut — both already staged with correct anchors. The production module itself is
the strongest artifact in the diff: every documented boundary in the spec's Edge-cases
section is either enforced in code or pinned by a named test, and I found no
correctness defect in `extensions/debug.py`.
