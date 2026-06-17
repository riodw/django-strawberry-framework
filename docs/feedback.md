# Final Review - spec-035 follow-up changes

No P1 production-code blocker found in the final batch. The two concrete test gaps from the previous
review are closed:

- `tests/optimizer/test_extension.py::test_mutation_real_execution_suppresses_only_keeps_select_related`
  now proves the G2 gate through a real Strawberry `mutation` execution, not only synthetic walker
  fixtures.
- `tests/types/test_resolvers.py::test_fk_id_elision_falls_back_on_real_deferred_only_instance`
  now proves the Decision 5 loaded-check against a real `Item.objects.only("name")` deferred
  instance, not only a hand-built double.

After reviewing the `0.0.10` through `0.0.14` cards, the remaining issues are
documentation/source-of-truth and benchmark-tooling problems. The later roadmap is broadly coherent:
`0.0.11` through `0.0.14` are still TODO/planned cards. The problematic area is the transition
boundary: both `0.0.10` cards are rendered in Done / shipped contexts, while public docs and card
body fields still mix current release, implemented-on-main, and planned language.

## Findings

### P2 - `0.0.10` generated board data still contradicts the implemented file set and shipped scope

`KANBAN.md` is generated from `examples/fakeshop/db.sqlite3`, so this is a source-data issue, not a
markdown-only typo. Reviewing both `0.0.10` cards widens the issue: the board puts
`DONE-034-0.0.10` and `DONE-035-0.0.10` in the Done column, but both card bodies still carry stale
planning-era data.

- `KANBAN.md #"#### Package files"` for DONE-035 lists only optimizer files and optimizer tests. It
  omits `django_strawberry_framework/types/resolvers.py` and `tests/types/test_resolvers.py`, even
  though Decision 5 shipped in the resolver layer and the new real deferred-instance coverage lives
  in `tests/types/test_resolvers.py`.
- `docs/builder/bld-final.md #"Files section now includes"` claims the DONE-035 Files section now
  includes `types/resolvers.py` and `tests/types/test_resolvers.py`; the generated board does not.
  That makes the build-final correction itself false.
- `KANBAN.md #"Spec file added under"` still says the spec was added under `docs/SPECS/`, and
  `KANBAN.md #"docs/SPECS/spec-<NNN>-optimizer_hardening-0_0_10.md"` still appears under Files
  likely touched. This conflicts with the corrected live-path rule now recorded in the spec DoD:
  `docs/spec-035-optimizer_hardening-0_0_10.md` stays in `docs/` until the next spec author's
  batched archive pass.
- `docs/spec-035-optimizer_hardening-0_0_10.md #"set the card's spec reference to docs/SPECS"` still
  repeats the stale Slice 4 card-completion instruction, even though the later DoD item correctly
  says the `SpecDoc` should point at the live `docs/spec-035-...` path.
- `KANBAN.md #"### [DONE-034-0.0.10 - Permissions subsystem]"` is in the Done column and its
  glossary table marks `apply_cascade_permissions` shipped, but the card header still says
  `Status: In progress`.
- The DONE-034 scope still says it ships "per-field permission hooks declared via `Meta`", while the
  same card's glossary table and `django_strawberry_framework/types/base.py #"fields_class"` show
  per-field hooks / `FieldSet` / `Meta.fields_class` are still planned for the later FieldSet work
  (`0.1.1`), not shipped in `0.0.10`. The actual package surface is the cascade helper
  (`django_strawberry_framework/permissions.py::apply_cascade_permissions` /
  `aapply_cascade_permissions`) plus the reserved `fields_class` slot.
- DONE-034's package file list is only `django_strawberry_framework/permissions.py (historical)`,
  despite the shipped implementation and tests spanning `django_strawberry_framework/permissions.py`,
  `django_strawberry_framework/utils/permissions.py`, `tests/test_permissions.py`, and integration
  tests around list/connection/node/optimizer surfaces.

Required correction: update the kanban DB rows for DONE-035, not just the rendered markdown, then
regenerate `KANBAN.md` and `KANBAN.html`; do the same reconciliation for DONE-034 while there. The
DONE-035 package files should include the resolver source and resolver tests, and the stale
`docs/SPECS/` per-card spec-placement text should be rewritten to the live-path lifecycle. DONE-034
should render terminal shipped state, describe only the cascade behavior that actually shipped in
`0.0.10`, and move the per-field hook wording to the later FieldSet card. Then either update or
remove the now-false post-build correction in `docs/builder/bld-final.md`.

### P2 - Public docs blur current release, implemented `0.0.10`, and planned `0.0.11`-`0.0.14`

The package metadata says the current version is `0.0.9`:

- `pyproject.toml #"version = \"0.0.9\""`
- `django_strawberry_framework/__init__.py #"__version__ = \"0.0.9\""`

The `0.0.11` through `0.0.14` cards are all still TODO/planned, so the roadmap itself is not the
problem. The problem is that public docs still say the current package is `0.0.8`, while also
describing `0.0.10` surfaces as shipped:

- `README.md #"**`0.0.8`, single-maintainer, alpha-quality.**"` is stale against the package
  metadata.
- `docs/GLOSSARY.md #"Current package version: `0.0.8`"` is also stale.
- `docs/README.md #"**Shipped today** (`0.0.8`):"` lists `0.0.9` and `0.0.10` features under a
  `0.0.8` heading.
- `docs/README.md #"**Coming next - remaining alpha (`0.0.10` -> `0.0.14`):"` still lists `0.0.10`
  as coming next immediately after describing `apply_cascade_permissions` and the optimizer
  robustness guards as shipped, while the board shows `0.0.11` through `0.0.14` are the remaining
  alpha TODO cards.

This leaves readers unable to tell whether `0.0.10` is available in the current package, implemented
on `main` but unreleased, or still pending. The card review changes the right correction: do not
describe `0.0.10` as just another future planned card, because both `0.0.10` cards are DONE; describe
it as implemented on `main` / pending the joint release cut unless the actual version bump has
already happened. The spec says the card must not bump version files, so the docs need precise
wording rather than another silent version drift.

Required correction: choose one explicit state and apply it consistently. If the repository is
post-`0.0.9` and pre-joint-`0.0.10` cut, say that in the public docs, mark the `0.0.10` surfaces as
implemented on `main` / pending release, and make the "coming next" list start at `0.0.11`. If the
joint cut has actually happened, then bump `pyproject.toml`, `django_strawberry_framework/__init__.py`,
and the version test together in the release change.

### P3 - `bench_plan_cache.py` reports cacheability from observed hit count, so small runs can lie

`scripts/bench_plan_cache.py::main #"cacheable = \"yes\" if warm_info.hits > 0 else \"no\""` derives
the `cacheable` column from whether the warm run happened to observe at least one cache hit. That is
not the same thing as the query being cacheable. With a legal small invocation:

```text
uv run python scripts/bench_plan_cache.py --iterations 1 --warmup 0 --seed 1
```

every candidate labelled `cacheable` in `CANDIDATES` printed `cacheable no` because a single warm
execution has one miss and zero hits. The same run also printed negative `walk us` deltas, which is
expected timing noise at one sample but misleading for a script that exposes those flags.

The README now uses this script for a public performance claim:
`README.md #"Benchmark ("` hard-codes default-run hit counts and microsecond deltas. That makes the
script's reporting contract more important than a private benchmark helper.

Required correction: separate "cacheable by plan" from "hits observed in this run". Either derive
cacheability from the built plan / cache-entry behavior, or prime the warm run with at least two
unmeasured executions before measured output. For low-sample invocations, print "insufficient
samples" or suppress `walk us` instead of reporting negative saved work as if it were meaningful.
For README, either move the exact numbers into sample output with machine/context details or describe
them as one benchmark run, not a stable package property.

### P3 - New cross-file links violate the standing reference-style Markdown rule

The new benchmark references use inline cross-file links in standing docs:

- `README.md #"Benchmark ([`scripts/bench_plan_cache.py`](scripts/bench_plan_cache.py)"`
- `BACKLOG.md #"Extend [`scripts/bench_plan_cache.py`](scripts/bench_plan_cache.py)"`

`AGENTS.md` requires standing docs/specs to use reference-style cross-file links, with definitions in
the unified bottom block under the canonical path group headers. README already follows that style
elsewhere, so the new inline link is visible drift.

Required correction: replace these with reference-style links, for example `[bench-plan-cache]`, and
add the definition under each file's `<!-- scripts/ -->` link-definition group.

## Verification performed

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-035-optimizer_hardening-0_0_10.md`
  passed with `OK: 23 terms`.
- `uv run python scripts/bench_plan_cache.py --iterations 1 --warmup 0 --seed 1` completed and did
  not dirty `examples/fakeshop/db.sqlite3`.
- Reviewed the rendered `0.0.10` through `0.0.14` KANBAN cards. `0.0.10` is rendered as DONE, while
  `0.0.11` through `0.0.14` are TODO/planned.
- `git status --short` was clean before overwriting this file.

Per repo instruction, I did not run pytest.
