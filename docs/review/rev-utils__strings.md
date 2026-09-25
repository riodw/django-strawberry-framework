# Review: `django_strawberry_framework/utils/strings.py`

Status: verified
Run: 0.0.15 2026-09-24-1
Path class: hot - the optimizer walker calls `snake_case` once per selection on every plan build (plan-cache miss, every non-cacheable request); every other helper runs at declaration, finalize or behind an upstream memo

## Implementation (Worker-2)

Pass 1. Item scratch `docs/review/temp-tests/utils__strings/implement/`. Every run below is at
address `review/utils/strings.py/implement` unless it says `before`. No dirty path at start
(`git status --short` showed only the five untracked review docs and `output/`), so no hunk
attribution was needed; the item diff (`git diff 6ac69870 -- <12 paths>`) holds only the hunks
below.

### Performance

- **L1 `_plain_text` exact-`str` first — implemented.** Rides on `utils/strings.py`, which F1-F4
  (Medium) change. `utils/strings.py::_plain_text` now tests `type(value) is str` first, then the
  `isinstance` rejection, then `str.__str__`. Probe `docs/review/temp-tests/utils__strings/performance/probe_plain_text.py`
  run by absolute path, so the `before` copy was not edited:
  - before `review-20260925T034653-e76c46` (`workspace.py run review/utils/strings.py/before --
    python <root>/performance/probe_plain_text.py <root>/implement/probe_plain_text.before.json`),
    digest `sha256:df761b82...9f3130` (= bench baseline): `plain_text shipped` 36.7 ns vs
    `reordered` 28.3 ns, delta 8.4 ns; `snake_case` 66.1 vs 61.5 ns; `parity: ok`.
  - after `review-20260925T035407-988276` (same command, `<root>/implement/probe_plain_text.after.json`,
    final tree, digest `sha256:a7408aee...c703e8`): `plain_text shipped` 29.3 vs `reordered` 28.7,
    delta 0.6 ns (Proof bound <= 2.0); `parity: ok`. An earlier after run on the L1-only tree,
    `review-20260925T034703-3e13b6`: delta -0.2 ns.
  - Must-not-change pinned by `tests/utils/test_strings.py` (44 passed, run
    `review-20260925T035345-9110fa`). No bench figure moves; nothing for `## Bench baseline`.

### Mechanics

- **M1 `field_map` keyed by the raw Django name — implemented at the owner.**
  - `types/base.py::DjangoType.__init_subclass__` builds `{f.name: FieldMeta...}`;
    `types/base.py::_validate_relation_shape_targets`, `types/base.py::_build_annotations`,
    `types/finalizer.py::_synthesize_relation_connections`, `types/finalizer.py::finalize_django_types`
    and `management/commands/inspect_django_type.py::Command._resolve_row` index by the Django
    name; the three `snake_case` imports are gone. Walker code unchanged (its three
    `snake_case(sel.name|graphql_name)` calls stay; a reverse miss forward-resolves through
    `optimizer/walker.py::_field_by_graphql_name`, as the record predicted).
  - Docstrings the key change made stale: `types/relations.py::PendingRelation`,
    `optimizer/walker.py::_resolve_field_map`, and one the record did not name,
    `types/__init__.py`'s dependency paragraph (listed `snake_case` among the helpers `types/`
    consumes; it no longer imports it). `tests/types/test_finalizer.py::test_malformed_pending_field_name_is_rejected_before_relation_lookup`
    docstring said the record "cannot leak ``snake_case`` AttributeError"; now it states the
    `ConfigurationError` it asserts (the lookup raises `KeyError`, wrapped by the existing
    `except BaseException`).
  - Test-local map builders copying the old rule now key by `field.name`:
    `tests/optimizer/test_walker.py` (three sites + import), `tests/optimizer/test_multi_db.py`,
    `tests/types/test_relay_interfaces.py`.
  - Permanent tests, package tier (no fakeshop model carries a mixed-case field and an item adds
    no example model: **missing fixture for `## Decisions`** = a fakeshop model with a mixed-case
    scalar, forward FK and reverse `related_name`, which would move both rows to
    `examples/fakeshop/test_query/`):
    - `tests/optimizer/test_extension.py::test_mixed_case_model_field_selection_projects_its_real_column`
      (the Proof's node): synthetic `managed = False` `isPublic` model under
      `DjangoOptimizerExtension`; asserts no errors, data `[{"id": pk, "name": "a", "isPublic": True}]`,
      exactly 1 query whose SQL carries `"isPublic"`, then
      `sorted(field_map) == sorted(selected field names)`. Wire assertions come first so the
      failability run shows the wire failure, not only the key assertion.
    - `tests/optimizer/test_extension.py::test_mixed_case_relation_selections_plan_through_their_django_names`
      (beyond the Proof, answering the Mechanics handoff's attack list): forward FK `ownerRef` and
      reverse `related_name="petItems"`, at 1 and 3 owners; pets list = 1 query w/ JOIN selecting
      `"displayName"`, owners list = 2 queries (root + prefetch filtering on `"ownerRef_id"`),
      counts `{1: (1, 2), 3: (1, 2)}`; field-map keys = Django names on both types.
    - Focused, shared tree: `uv run pytest tests/optimizer/test_extension.py -k mixed_case --no-cov -n0`
      2 passed; with `tests/types/test_finalizer.py::test_malformed_pending_field_name_is_rejected_before_relation_lookup`
      and `tests/utils/test_strings.py`: 44 passed.
  - Proof (3): `rg -n "snake_case\(" django_strawberry_framework/types django_strawberry_framework/management`
    0 lines; walker count 3.
  - Proof (4) + new nodes: `review-20260925T035353-5891aa` (`pytest tests/types/test_definition_order.py::test_camel_case_field_collision_raises
    tests/optimizer/test_walker.py tests/optimizer/test_multi_db.py tests/types/test_relay_interfaces.py
    tests/types/test_finalizer.py <two new nodes> --no-cov -q`, copy fresh): 351 passed.
  - Whole default suite in the copy, `review-20260925T035001-6271cb` (`pytest --no-cov -q`, before
    the assertion reorder in the two new tests, production code identical): 8852 passed, 40
    skipped, 2 failed, both `tests/test_ci_governance.py` (`test_the_sweep_corpus_covers_every_committable_python_file`,
    `test_the_git_oracle_enumerates_this_module`): `git ls-files` exits 128 because a workspace
    copy holds no `.git`. Environmental; the gate copy carries a git index.
  - Cells: sharded and pg not run; the target and M1 reach no alias or dialect decision (the
    failure is `QuerySet.only` / `select_related` name resolution in model metadata), as the
    record states.

### Comments

- **F1 module docstring — implemented** with the record's text, adjusted per the Cross-axis note:
  `snake_case`'s bullet names the walker only ("reverses each selection name with it to find the
  Django field, then matches the forward name where the reversal is lossy"), not the field maps.
  First line unchanged, so no TREE.md render; `build_tree_md.py --list-docstrings` `ok`.
- **F2 `snake_case` contract — implemented.** `"__doc__"` dropped from `functools.wraps`'
  `assigned`; contract moved onto `snake_case`; `_snake_case_cached` one line. Text as proposed
  plus one more unrecoverable boundary M1 made relevant: "an upper-case letter the Django name
  already carries (``isPublic`` stays ``isPublic``, which reverses to ``is_public``)".
- **F3 `graphql_camel_name` — implemented** (first line, head/capitalize sentence, marker rule
  "only between two uppercase characters").
- **F4 `pascal_case` — implemented** (first line, interior paragraph, acronym paragraph; the
  "cannot contain upper-case" and "acronym caveat" claims are gone).
- **F5 `_plain_text` — implemented**, rides on F1-F4; the docstring also states why the exact-`str`
  test runs first (L1).
- **F6 `pascal_case_or_raise` first line — implemented**, rides on F1-F4.
- **F7 `flatten_lookup_path` — implemented**, rides on F1-F4.
- **F8 test-module provenance — deferred:** Low, and no higher finding changes
  `tests/utils/test_strings.py` (REVIEW "Severity"). Its Proof still prints `2`.
- Proof lines, all run after the edits: F1 `True True True True`; F3 `True`; F4 `True True`; F5
  `True`; F6 `True`; F7 `True True`; F2 `review-20260925T035345-4a042c` prints
  `True True True True` and `test_snake_case_preserves_lru_cache_controls` passes
  (`review-20260925T035345-9110fa`).

### Failability

Manifest `docs/review/temp-tests/utils__strings/implement/proofs.json`, pre-images
`base.pre.py`, `finalizer.pre.py`, `inspect.pre.py`, `strings.pre.py` (each
`git show 6ac69870:<path>`), run `workspace.py prove review/utils/strings.py/implement <manifest>`:

- `review-20260925T035329-f06d73`, exit 0:
  1. M1 (three sites restored to the baseline): pinned, the 2 failing rows are exactly the
     declared `expect_failing` (both new nodes), each crashing on `result.errors` =
     `GraphQLError('An unexpected error occurred.')` (`MixedCaseFlag has no field named
     'is_public'`, `MixedCasePet has no field named 'owner_ref'`); unmutated scope 2 passed.
  2. `utils/strings.py` restored to the baseline over `tests/utils/test_strings.py` +
     `tests/utils/test_init.py`: behaviour preserved, `expect_failing: []` met (44 passed both
     runs).
- Superseded runs: `review-20260925T035225-9b1a3e` (M1 pinned, but only on the key assertion,
  before the reorder); `review-20260925T035307-0da5c6` (INVALID COUNT: `prove_failability.py`
  counted six pytest captured-log lines, `ERROR    strawberry.execution:...`, as collection/setup
  errors). The M1 scope now carries `--show-capture=no`, which removes those lines.

### Lint

On the 12 touched paths: `ruff check --fix`, `check_trailing_commas.py`, `ruff format` (2 files
reformatted), then `ruff check` passed, `ruff format --check` 12 already formatted,
`check_trailing_commas.py --check` 0 violations, `check_citations.py --check` 1280 citations
resolve. Re-run on `tests/optimizer/test_extension.py` after the assertion reorder: clean.

### Fingerprints (`git hash-object`, 12 chars)

`utils/strings.py` 536d175cd605; `types/base.py` 49057fad2058; `types/finalizer.py`
de34ae2aaed1; `types/relations.py` 4098eebca9b9; `types/__init__.py` 1bf69028dbdc;
`optimizer/walker.py` 73d6929a5881; `management/commands/inspect_django_type.py` 2807d0fc9d75;
`tests/optimizer/test_extension.py` 4101bbd3805e; `tests/optimizer/test_multi_db.py`
16753577c693; `tests/optimizer/test_walker.py` 7a76159a24f6; `tests/types/test_finalizer.py`
05e1c9ecf621; `tests/types/test_relay_interfaces.py` bea2afd41616. Read, unchanged:
`types/resolvers.py` 72d62dc4ebfe, `optimizer/extension.py` e0e53a8e10fc,
`optimizer/nested_planner.py` b4dfd4a6f610, `types/definition.py` fa6c4d330e72,
`tests/utils/test_strings.py` 3dad1a9d42d8. Package paths relative to `django_strawberry_framework/`.

### Proposed owned changes

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/utils/strings.py` | utils/strings.py | Performance, Comments | `_plain_text` (branch order, docstring); module docstring; `_snake_case_cached` docstring; `snake_case` (`functools.wraps` `assigned`, docstring); `pascal_case`, `pascal_case_or_raise`, `graphql_camel_name`, `flatten_lookup_path` docstrings |
| `django_strawberry_framework/types/base.py` | utils/strings.py | Mechanics | `DjangoType.__init_subclass__` (field-map key), `_validate_relation_shape_targets`, `_build_annotations`; `snake_case` import removed |
| `django_strawberry_framework/types/finalizer.py` | utils/strings.py | Mechanics | `_synthesize_relation_connections`, `finalize_django_types`; `snake_case` import removed |
| `django_strawberry_framework/management/commands/inspect_django_type.py` | utils/strings.py | Mechanics | `Command._resolve_row`; `snake_case` import removed |
| `django_strawberry_framework/types/relations.py` | utils/strings.py | Mechanics | `PendingRelation` docstring |
| `django_strawberry_framework/optimizer/walker.py` | utils/strings.py | Mechanics | `_resolve_field_map` docstring |
| `django_strawberry_framework/types/__init__.py` | utils/strings.py | Mechanics | module docstring (dependency paragraph) |
| `tests/optimizer/test_extension.py` | utils/strings.py | Mechanics | `_unmanaged_tables`, `test_mixed_case_model_field_selection_projects_its_real_column`, `test_mixed_case_relation_selections_plan_through_their_django_names` (new) |
| `tests/optimizer/test_walker.py` | utils/strings.py | Mechanics | `_register_type_definition`, `test_scalar_only_secondary_resolver_uses_secondary_field_map`, `test_optimizer_walker_uses_primary_for_nested_relation_target`; `snake_case` import removed |
| `tests/optimizer/test_multi_db.py` | utils/strings.py | Mechanics | `_register_type_definition`; `snake_case` import removed |
| `tests/types/test_relay_interfaces.py` | utils/strings.py | Mechanics | `_field_map_for`; `snake_case` import removed |
| `tests/types/test_finalizer.py` | utils/strings.py | Mechanics | `test_malformed_pending_field_name_is_rejected_before_relation_lookup` docstring |

Handoff: Read beyond the records: `types/definition.py` field-map invariants, `types/resolvers.py`
and `optimizer/nested_planner.py` raw-key lookups (already raw, now agree), `optimizer/extension.py`
hint lookup (now agrees), every `field_map[...]` / `.field_map` reader in the package (all now
index by the Django name; the walker alone reverses GraphQL names), `tests/_relation_fixtures.py`
and `tests/test_relay_connection.py` for the unmanaged-table pattern, `scripts/prove_failability.py`
manifest format. Open threads: (1) not run: the async flavor and the Relay/connection shape
(`relation_shapes` on a mixed-case reverse relation, `relation_connections` slot keys are
`<name>_connection` with the raw name, so `snake_case(selection)` misses and the loop over
`graphql_names` resolves it); the Mechanics verifier's attack list names both. (2)
`tests/optimizer/test_walker.py` carries pre-existing past-tense narrative in docstrings this
item did not write (`test_plan_elides_forward_fk_when_target_pk_is_digit_boundary_name`: "reversed
each pk selection ... The helper now forward-resolves"; the `printings_2` connection test: "The
walker reversed ... Before the consolidated forward resolver"); the Comments verifier may grade
them since the item touches the file; I left them because no record raised them. (3)
`prove_failability.py` misreads pytest's captured-log `ERROR <logger>` lines as setup errors; any
proof whose failing rows log at ERROR needs `--show-capture=no` in its scope. That is a script
defect outside this item, reported to Worker-0. (4) `utils/__init__.py` still frames `strings` as
"case conversion (``snake_case``, ``pascal_case``)"; the Comments handoff routes it to the
`utils/` folder item.

## Iterations

### Implement pass 2

Re-dispatch `revision-needed`: the Comments verifier's pass-1 gaps F9, F10, F11 (`verify 1`).
Performance and Mechanics verified in pass 1; this pass changes no code (inverse proof below), so
nothing on those axes moves. Address `review/utils/strings.py/implement`; scratch
`docs/review/temp-tests/utils__strings/implement/pass2/`.

Attribution: `git diff 6ac69870 -- <12 dirty paths>` was byte-identical to `diff/pass-1.diff`
before the first edit (`cmp`), and `optimizer/field_meta.py` was clean at HEAD (blob
7215c887aa26). After the edits the item diff is pass 1 plus exactly the three hunks below; 13
paths.

Gaps answered:

- **F9 `FieldMeta.name` (Medium) - implemented** at `optimizer/field_meta.py::FieldMeta`
  `Attributes:` entry: `name: The Django field's ``name`` as declared, in any letter case; the key
  of ``DjangoTypeDefinition.field_map``.` Shorter than the record's text: "on the model" dropped,
  since a reverse relation's `name` is its query name, declared on the other model's FK; no case
  claim beyond "as declared" (verifier handoff). True against `FieldMeta.from_django_field` /
  `_from_field_shape` (name passed through unchanged) and `types/base.py::DjangoType.__init_subclass__`
  (`{f.name: FieldMeta.from_django_field(f) ...}`). Proof: `rg -c "snake_case"
  django_strawberry_framework/optimizer/field_meta.py` prints nothing, exit 1;
  `rg -n "field_map"` shows the entry (line 65). Module first line unchanged.
- **F10 `snake_case` cache reason (Low) - implemented** in `utils/strings.py::snake_case`: "on
  every plan build (a plan-cache miss, or an uncacheable plan once per execution)". Wording
  refines the record's "an uncacheable operation": cacheability is per plan, and
  `optimizer/extension.py` reuses an uncacheable plan within one execution through the
  per-execution memo (`exec_memo`), so the walker reruns for it once per execution, not per call.
  Proof: `$P` form prints `True True`; F2's Proof re-run with F10's checks appended,
  `review-20260925T040930-66fb9d` (`workspace.py run review/utils/strings.py/implement --fresh --
  python -c "<F2 Proof expression>, 'every request' not in d, 'plan build' in d)"`), prints
  `True True True True True True`.
- **F11 broken `#"substring"` (Low) - implemented** in `tests/optimizer/test_multi_db.py` module
  docstring: `AGENTS.md #"Test through real usage, prefer the example project"`, quote on one
  source line. Proof: `check_citations.py --paths tests/optimizer/test_multi_db.py --substrings`
  exit 0 ("4 citations resolve"). Over all 13 item paths: 66 resolve, 0 unresolvable.
- **F8** stays `deferred` (Low; `tests/utils/test_strings.py` still outside the item diff).

Inverse proof (docstring-only edits): pass-1 versions rebuilt in scratch from `git archive
6ac69870` + the two files' hunks of `diff/pass-1.diff` (`patch -p1`; blobs 536d175cd605 and
16753577c693 = pass-1 fingerprints), `field_meta.py` from HEAD; `pass2/ast_identity.py` compares
ASTs with every module / class / function docstring removed: all three `AST-identical`. Positive
control: the same script on HEAD `strings.py` vs the current file reports `DIFFERS` (L1's branch
reorder). No gate relied on, so no failability manifest; no permanent test owed for prose.

Focused, shared tree: `uv run pytest tests/utils/test_strings.py tests/optimizer/test_multi_db.py
--no-cov -n0 -q`: 42 passed.

Lint: `ruff check --fix`, `check_trailing_commas.py`, `ruff format` on the 3 touched paths (no
change); then on all 13 item paths `ruff check` passed, `ruff format --check` 13 already
formatted, `check_trailing_commas.py --check` 0 violations; `check_citations.py --check` 1280
resolve. `build_tree_md.py --list-docstrings` on the 3 paths: `ok`; no first line changed, no
TREE.md render.

Fingerprints (12 chars) after this pass: `optimizer/field_meta.py` 18ea719a6141; `utils/strings.py`
991f7dad20b3; `tests/optimizer/test_multi_db.py` 88298e98d462; the other ten item paths unchanged
from pass 1 (`inspect_django_type.py` 2807d0fc9d75, `optimizer/walker.py` 73d6929a5881,
`types/__init__.py` 1bf69028dbdc, `types/base.py` 49057fad2058, `types/finalizer.py` de34ae2aaed1,
`types/relations.py` 4098eebca9b9, `tests/optimizer/test_extension.py` 4101bbd3805e,
`tests/optimizer/test_walker.py` 7a76159a24f6, `tests/types/test_finalizer.py` 05e1c9ecf621,
`tests/types/test_relay_interfaces.py` bea2afd41616). Read, unchanged: `optimizer/extension.py`
e0e53a8e10fc.

Proposed owned changes (this pass; the pass-1 table stands, these rows add to or join it):

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/optimizer/field_meta.py` | utils/strings.py | Comments | `FieldMeta` docstring (`name` attribute) |
| `django_strawberry_framework/utils/strings.py` | utils/strings.py | Comments | `snake_case` docstring (cache reason) |
| `tests/optimizer/test_multi_db.py` | utils/strings.py | Comments | module docstring (AGENTS.md citation) |

Handoff: Read beyond the gaps: the plan-cache and per-execution memo path in
`optimizer/extension.py` (the source of F10's wording), `FieldMeta._from_field_shape`. The
Comments verifier regrades three texts; Performance and Mechanics need no re-run (no code moved,
AST identity above). `git apply` run from a directory inside the repo applies relative to the
repo root and skips silently when paths do not match; rebuild pre-images with `patch -p1 -d` or
`workspace.py path`. Open threads from pass 1 unchanged: `utils/__init__.py`'s two-helper
framing (folder item), `tests/optimizer/test_walker.py` provenance (walker item), the walker
miss-path cost (walker item), `prove_failability.py`'s captured-log miscount, the mixed-case
fakeshop fixture for `## Decisions`.
