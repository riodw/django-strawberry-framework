# Feedback — `docs/spec-021-filters-0_0_8.md`

Three findings on the spec document itself. The spec is in good shape after rev5; these are residual gaps a final pass should close.

---

## H — must-fix before implementation

### H1 — Test plan doesn't cite the canonical reload fixture by name

[Test plan](spec-021-filters-0_0_8.md#test-plan) ends with a single-line footnote:

> "The HTTP test file's reload pattern from `docs/TREE.md` is preserved: clear the global registry, reload app schema modules, then reload the project schema and URLconf."

The implementer reading the spec doesn't get pointed at the fixture they should reuse. The actual fixture lives at [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`](../examples/fakeshop/test_query/test_library_api.py), and the README at [`examples/fakeshop/test_query/README.md`](../examples/fakeshop/test_query/README.md) names it as the canonical shape for the test tree. Two specific issues:

1. **"Preserved" is the wrong verb.** The spec is the first card adding 13 new tests to `test_library_api.py` — it reuses the existing fixture; it doesn't preserve a pattern.
2. **The reference points at `docs/TREE.md`,** not the README or the fixture. An implementer following the link reads about the test-tree layout but not the fixture shape.

**Fix:** Replace the footnote with something like:

> "All 13 new live HTTP tests reuse the existing `_reload_project_schema_for_acceptance_tests` fixture from [`examples/fakeshop/test_query/test_library_api.py::_reload_project_schema_for_acceptance_tests`](../examples/fakeshop/test_query/test_library_api.py); the fixture clears the global registry, reloads `apps.library.schema`, reloads `config.schema`, reloads `config.urls`, and clears URL caches. The spec's filter binding plumbs through phase 2.5 on the reload, so the fixture continues to work without modification."

Cite the fixture by symbol-qualified path (matches the spec's existing source-reference convention).

### H2 — `Book.title` described as `CharField`; it's `TextField`

The new `tests/types/test_definition_relations.py` description in [Test plan](spec-021-filters-0_0_8.md#test-plan) says:

> "`related_target_for("title")` (a scalar `CharField`) returns `None`"

I verified directly against [`examples/fakeshop/apps/library/models.py::Book`](../examples/fakeshop/apps/library/models.py): `title = models.TextField()`. The only `CharField` on `Book` is `circulation_status` (which carries `choices=...` — the documented exception). The spec describes a field that doesn't match the fakeshop model.

**Fix:** Replace "a scalar `CharField`" with "a scalar `TextField`" in the test description. If you want the test to actually exercise a `CharField` for type-coverage reasons, switch the field to `Book.circulation_status` — but `title` is the more obvious example, and the description fix is the natural answer.

---

## L — nits

### L1 — Venv path in [Borrowing posture](spec-021-filters-0_0_8.md#borrowing-posture) is machine-specific and Python-version-pinned

The spec cites `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/` in four places. The path works on the maintainer's machine today but won't resolve for any other reader or any future Python upgrade.

**Fix:** Normalize to `~/projects/django-graphene-filters/.venv/lib/python*/site-packages/graphene_django/...` (tilde + version glob) in all four occurrences. Same finding as the prior review's L4; not blocking, but worth catching in the same pass as H1/H2.

---

## What's strong

- Rev5 carried ~90% of the rev4 feedback through to the body; the residual sweep items flagged in the prior round are mostly the remaining work, and the rev6 contents on top of those will get the spec to implementation-ready.
- The named-helper decomposition in [Decision 8](spec-021-filters-0_0_8.md#decision-8--relation-permission-cascade--get_queryset-cooperation) is a genuinely good seam for tests.
- The orphan-FilterSet check (H5 of rev5) closes a real footgun.
- The `apply_sync` / `apply_async` split honors the security-correct ordering without imposing async on sync resolvers.

---

## Suggested order

H1, H2, L1 are all single-paragraph or single-word edits, independent of each other and of the rev6 carryover sweep. Roll them into the same pass that closes the rev5 sweep items.
