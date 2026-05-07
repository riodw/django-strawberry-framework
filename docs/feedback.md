
## New observations on the working-tree diff (F-1 through F-12)

### F-1. The entire `apps/` and `config/` trees are untracked, and every old path is staged for deletion

After unstaging, `git status` shows:

- `D` (delete) entries for every file under `examples/fakeshop/library/`, `examples/fakeshop/products/`, plus `examples/fakeshop/{__init__.py, schema.py, settings.py, urls.py, wsgi.py}`.
- Two untracked directories: `examples/fakeshop/apps/` and `examples/fakeshop/config/`.

Git no longer sees these as renames — it sees a full-tree deletion plus an unrelated untracked addition. If the user commits the `D` entries without `git add`-ing the new directories, the example project is broken in that commit (no settings, no urls, no models, no schema, every package test that imports `apps.products.models` or `apps.library.models` fails). On a follow-up commit that adds `apps/` and `config/`, git will likely **not** detect the rename across the two commits, so the file history loses the rename connection and `git log --follow examples/fakeshop/apps/library/models.py` will not walk back into the previous `examples/fakeshop/library/models.py` history.

Two concrete recommendations:

1. **Stage everything together in one commit** so git records the renames atomically. From the repo root:
   ```shell path=null start=null
   git add examples/fakeshop/apps examples/fakeshop/config
   git add -u examples/fakeshop
   ```
   The first command picks up the untracked tree (both new directories and every file under them); the second stages the matching deletions of the old paths (`-u` updates tracked files only, including deletions). Then `git status` should show the changes as renames again, and a single commit preserves the history.

2. **Verify before committing.** After staging, run `git --no-pager status` and confirm the lines read `R` (rename) rather than `D` (delete) + `A` (add). With Git's default rename detection threshold this should happen automatically once both sides are staged; if anything still shows as separate delete+add, raise the rename threshold for the commit (`git config diff.renames true` is the default, but `git -c diff.renames=copies` or higher similarity may be needed for files that were also content-edited during the move).

Also confirm the untracked `apps/__init__.py` and `config/__init__.py` are present and tracked after staging — Python's import machinery for `apps.library.apps.LibraryConfig` and `from config.schema import schema` walks regular-package machinery, and a tree where `apps/` and `config/` are namespace packages can produce subtler shadow-import behavior under tooling that adds other paths to `sys.path`.

### F-2. The override resolver in `BranchType.shelves` quietly defeats the optimizer

```python path=/Users/riordenweber/projects/django-strawberry-framework/examples/fakeshop/apps/library/schema.py start=62
    @strawberry.field
    def shelves(self) -> list[ShelfType]:
        """Consumer-authored relation resolver used by HTTP override tests."""
        return list(self.shelves.order_by("-code"))
```

`self` here is the resolved `Branch` Django instance, so `self.shelves` is the reverse-FK related manager. `.order_by("-code")` returns a fresh queryset that is **not** the queryset Django prefetched; the prefetch cache only matches by exact queryset signature, so this resolver bypasses any optimizer-planned prefetch.

That is the foundation contract — consumer-overridden relation fields suppress the framework's resolver — but it has an implication: the override is N+1-prone. With one branch, the cost is invisible (1 root query + 1 manager query = 2 queries). With N branches, it becomes 1 + N.

`test_library_relation_override_shapes_http_response_data` does **not** assert query count, so a regression where this resolver is invoked per-branch unexpectedly is silently uncovered. Two cheap pins, in increasing strength:

1. Add a `CaptureQueriesContext` to that test and assert the query count for one branch (sets the baseline).
2. Add a second test that seeds two branches and asserts the count is 3 (root + 2 per-branch shelf queries), which documents the override's N+1 cost in code.

This is also worth flagging as a documentation point in `docs/FEATURES.md` under the manual-override section: "Consumer overrides that re-shape the queryset (`.order_by(...)`, `.filter(...)`) bypass the framework's prefetch plan and may cause N+1 lookups."

### F-3. `OptimizerHint.SKIP` test relies on the seed shape having exactly one `Loan`

`test_library_optimizer_hints_are_observable_over_http` asserts `len(captured_skip) == 2` for the SKIP path: 1 root query + 1 lazy-loaded `library_patron` lookup. That count holds because `_seed_library_graph()` creates exactly one Loan. With two Loans, the count would be 3 (root + 2 lazy patron loads); with N, it would be 1 + N. The test would fail in confusing ways if a future seed change added a second Loan.

This is a hidden test-data contract that should be made explicit. Either:

- Add a comment above the SKIP assertion: `# Seed has exactly one Loan; SKIP causes lazy loading, so count is 1 + 1 (root + per-Loan patron lookup).`
- Or seed two Loans and assert `len(captured_skip) == 3`, which makes the N+1 nature of SKIP visible.

The second form is more honest: SKIP **is** an opt-in N+1 hint, and the test should pin that semantic, not hide it behind a one-row seed.

### F-4. AGENTS.md still references the bare module name `products.services` (not `apps.products.services`)

```text path=/Users/riordenweber/projects/django-strawberry-framework/AGENTS.md start=18
## First step of every test: seed via services
products.services exposes seed_data(count=N), create_users(count=N), …
```

Anywhere a contributor reads that line as an importable path, they get `ModuleNotFoundError`. The actual import path under the new layout is `apps.products.services`. Same for any other dotted-module reference in AGENTS.md (`tests/types/test_definition_order.py` already uses `from apps.products.services import ...` correctly; the AGENTS.md prose is the stale surface).

One-line fix: `apps.products.services exposes …`.

### F-5. The default seed helper is still over-eager for tests that do not need the full graph

Five HTTP tests call `_seed_library_graph()` which creates 8 rows (Branch + Shelf + Genre + Book + Patron + MembershipCard + second Patron + Loan). Of those:

- `test_library_optimizer_selects_book_shelf_in_http_query` queries only `allLibraryBooks { title shelf { code } }` — needs Branch + Shelf + Book.
- `test_library_choice_enum_and_nullable_subtitle_are_deliberate_http_contracts` queries `allLibraryBooks { title subtitle circulationStatus }` — needs Shelf + Book.
- `test_library_optimizer_hints_are_observable_over_http` queries Loans — needs Branch + Shelf + Book + Patron + Loan; does not need MembershipCard, Genre, second Patron.

`_seed_branch_with_two_shelves()` shows the right pattern. Most of the optimizer-shape tests would benefit from narrower helpers (`_seed_book_with_shelf()`, `_seed_loan_with_book_and_patron()`) so each test's setup cost matches its assertion shape. Not a blocker; it does compound as the suite grows.

### F-6. `apps/library/__init__.py` has trailing whitespace; the new `apps/__init__.py` and `config/__init__.py` are single-blank-line

The three init files diverge slightly:

- `apps/__init__.py` — one byte (single newline)
- `config/__init__.py` — one byte
- `apps/library/__init__.py` — two newlines (carryover from the round-5 file)
- `apps/products/__init__.py` — also from the round-5 file

Cosmetic. `ruff format` does not normalize empty `__init__.py` files. If anybody cares, normalize them all to a single trailing newline.

### F-7. `examples/fakeshop/__init__.py` deletion is correct, but worth a one-line note

The deletion is consistent with the new layout: `examples/fakeshop/` is no longer a Python package, just a project directory. With `pythonpath = examples/fakeshop`, `config` and `apps` resolve as bare top-level packages. ✅

But: a contributor who was used to writing `from fakeshop.products.models import ...` (as several round-3 tests did) will see the rename hit and might be confused why `examples/fakeshop/__init__.py` was deleted. A one-sentence note in `docs/TREE.md` or AGENTS.md explaining "Project root is a directory, not a package; `apps/` and `config/` are the importable packages, both reachable via `pythonpath = examples/fakeshop`" would prevent the confusion.

### F-8. The `BranchType.shelves` override illustrates a name-shadowing pattern worth documenting

The class declares both:

- `shelves` as a `@strawberry.field`-decorated method (consumer-authored).
- `Meta.fields = ("id", "name", "city", "shelves")` listing `"shelves"` as a Django reverse-FK field.

The framework's relation-override contract correctly resolves this: the class-dict value is detected as a `StrawberryField`, the field is added to `consumer_assigned_relation_fields`, and the finalizer skips auto-resolver attachment for it. Functionally clean.

But: the `shelves` symbol is overloaded. Inside the resolver body, `self.shelves` refers to the Django related manager (because `self` is the Django model). At the class level, `BranchType.shelves` refers to the StrawberryField object. This is exactly the pattern the foundation slice's relation-override contract was designed to support, and it is worth promoting `apps/library/schema.py` (or a focused snippet from it) into `docs/FEATURES.md` as a "manual relation override" reference.

The same file also showcases `Meta.optimizer_hints` (`LoanType`), choice-field handling (`Book.circulation_status`), and nullable scalars (`Book.subtitle`). It is now the most complete shipped-API reference in the repo.

### F-9. The `_seed_library_graph` helper creates rows in an order that depends on the migration's table layout

The helper does `Branch.objects.create(...)` first, then `Shelf`, then `Genre`, then `Book`, then `book.genres.add(genre)`, then `Patron`, etc. The order is correct given the FK constraints, but if a future migration reorders fields or adds a `NOT NULL` column without a default, the helper breaks silently (only when running the suite). Not actionable today; worth keeping in mind.

### F-10. `docs/TREE.md`'s "current on-disk layout" section is up to date but still references `apps.py` as a target file

`docs/TREE.md:226` is in the "target layout" block (post-Layer-3) and lists `apps.py` as a top-level package file. That is still planned (`BACKLOG-001` in KANBAN). Fine. But the surrounding prose at `:191` reads cleanly only if the reader understands the difference between "the current on-disk layout" (just above) and "the target layout" (just below). Worth a one-line subhead break between the two so readers do not conflate them.

### F-11. `docs/spec-testing_shift.md`'s `## Remaining follow-ups` section is thin

The new `## Remaining follow-ups` section says: "Future slices can still migrate more optimizer extension cases from `tests/optimizer/test_extension.py` into live HTTP tests where the behavior is consumer-visible." That is correct but unactionable. If the user intends this spec to be a contributor onboarding ramp for future Layer-3 acceptance work, the follow-ups should be enumerated, not gestured at. Two concrete bullets that match the round-5 migration list:

- Strictness mode (`tests/optimizer/test_extension.py:1275-1381`) — lift to HTTP if a debug header / test-only extension surfaces planned-key state on the response.
- B8 queryset-cooperation diff cases (`:2277-2354`) — partially covered by `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http`; the cases that exercise consumer `Prefetch(...)` objects with custom queryset shapes are not yet HTTP-covered.

Alternatively, archive this spec entirely (move to `docs/archive/spec-testing_shift.md`) and let `KANBAN.md` track the residual work.

### F-12. `tests/fixtures/__pycache__/` is still on disk

Round-5 M-10. `efa31fc` deleted the fixture files but the `__pycache__` directory remains. `rm -rf tests/fixtures` cleans it up. Worth a one-line `.gitignore` entry too if it is not already covered by the global `__pycache__/` rule.

## Recommended priority order

1. **F-1** — stage the new `apps/` and `config/` trees alongside the old-path deletions in the same commit so git records renames (1–2 minutes; **must** happen before commit, otherwise history loses the rename connection and CI sees a transient broken commit).
2. **F-4** — fix the `products.services` → `apps.products.services` reference in AGENTS.md (1 minute).
3. **F-2** — add a query-count assertion to the override HTTP test (10 minutes).
4. **F-3** — make the `OptimizerHint.SKIP` N+1 contract explicit (5 minutes — comment, or 15 minutes — re-seed and re-assert).
5. **F-12** — clean up `tests/fixtures/` (1 minute).
6. **F-7, F-10, F-11** — small documentation tightening (10 minutes total).
7. **F-5** — narrower seed helpers (45 minutes; optional).
8. **F-6, F-8, F-9** — cosmetic / forward-looking; defer.

## Closing note

This round's diff resolves the bulk of the round-5 follow-ups and brings the example project into a recognized cookiecutter-django-shaped structure. The HTTP test surface now covers every category the testing-shift spec called out: nested traversal, OneToOne nullability, M2M reverse, choice enums, nullable scalars, consumer-shaped querysets, optimizer hints, and consumer relation overrides. The two new in-process tests (`test_project_schema_includes_library_types` and `test_library_djangotype_declaration_order_stays_awkward`) close the smoke-test and regression-pin asks from round-5.

The most important pending item is purely procedural: **stage the new `apps/` and `config/` trees together with the old-path deletions in the same commit** so git records the renames atomically. After that, the diff is shippable.
