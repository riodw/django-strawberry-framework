# Review: docs/spec-018-export_schema-0_0_7.md

## High

No high-severity findings.

## Medium

- The rev2 `docs/TREE.md` prose-cleanup requirement is still missing from the dedicated `Doc updates` section. Revision history, the Slice 3 checklist, and Definition of done now correctly require removing `, and the management command` from the current-on-disk-layout prose, but the later `Doc updates` → `docs/TREE.md` bullet still lists only: add the current `management/` subtree, remove the target-layout `[alpha]` tag, and add `tests/management/`. That section is the implementation-facing doc-update checklist; if a worker follows it literally, `docs/TREE.md` can still ship with the stale sentence saying the management command is not on disk yet. Add the prose-fragment removal there too, matching the Slice 3 checklist and DoD.

## Low

- `Goals` item 3 still says `tests/management/test_export_schema.py` covers "the four contracts pinned in Test plan." The Test plan now specifies seven package-internal tests after the rev2 correction. If "four contracts" is meant as a grouping rather than a test count, name the groups explicitly; otherwise update this to the seven-test contract so the Goals section no longer reads like rev1 residue.

- The strawberry-django borrowing section still describes only "two forced divergences" and says the repo adds one module docstring and one class docstring. Rev2 correctly adds method docstrings and annotations in Decision 2, the Slice checklist, Edge cases, and DoD, so this earlier explanatory section should be updated to avoid reintroducing the old incomplete gate story. The later Decision 2 paragraph also says "all four divergences" while itemizing more than four individual deltas; grouping these as categories would make the count unambiguous.

- Decision 5 opens with "`handle()` raises Django's `CommandError` ... in three shapes," but the missing-positional shape is raised by Django's argparse layer before `handle()` runs. The body explains that correctly, so this is just wording drift; rephrase the opening as "the command surfaces `CommandError`" or split the pre-`handle()` argparse case from the two `handle()` branches.

- The synthesized-module tests should specify cleanup/isolation via `monkeypatch.setitem(sys.modules, "test_module", module)` or an equivalent fixture. The current plan correctly uses explicit `:symbol` selectors, but it leaves `test_module` in `sys.modules` unless the implementer infers cleanup. Pinning the fixture shape prevents cross-test pollution and keeps the seven tests order-independent.

## Verified resolved from prior review

- The previous High finding about `D102` / `ANN001` / `ANN201` is resolved in the normative implementation sections: the spec now pins method docstrings, `CommandParser`, and `-> None` returns, and correctly removes the false package-source per-file-ignore claim.
- The previous missing-positional test gap is resolved in the Test plan, implementation table, Slice checklist, and DoD: the package-internal test list now has seven tests and covers both `ImportError` and `AttributeError` branches.
- The previous non-schema selector issue is resolved in the user-facing example and package test plan: `config.urls:urlpatterns` and explicit `test_module:not_a_schema` selectors now target non-schema objects.
- The previous `docs/TREE.md` prose issue is partially resolved in revision history, Slice 3 checklist, and DoD; only the dedicated `Doc updates` section still needs the same propagation.

## Verification notes

- `git status --short --untracked-files=all` returned clean before this feedback edit.
- `strawberry.utils.importer.import_module_symbol` still imports the selector as the module name when no `:symbol` suffix is present, then reads `default_symbol_name="schema"`.
- `examples/fakeshop/config/urls.py` exposes `schema` as the real Strawberry schema and `urlpatterns` as a list, so `config.urls:urlpatterns` is the correct non-schema example.
- A direct `print_schema(config.schema.schema)` sanity check confirms the fakeshop SDL contains `type Branch`, so the proposed live assertion is valid.
- `pyproject.toml` still has no package-source per-file ignore for `D102`, `ANN001`, or `ANN201`; the rev2 command-shape correction remains necessary.
