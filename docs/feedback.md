# Review feedback — `docs/spec-018-export_schema-0_0_7.md` (revision 4)

Reviewer pass against the rev4 spec, run after the rev3-feedback fixes landed. The rev4 corrections (M1 type-name, L1 negative-shape header, L2 handle-body comment, L3 `CommandParser.error()` mechanism, L4 DoD coverage-gate clause, I1 `: object` narrow justification) all verified intact against the spec body. The TODO-scaffolding pass through every relevant file in [the codebase](.) also surfaced nothing else that contradicts the spec.

Two findings: one medium-severity propagation gap from rev4 L3, one low-severity inaccuracy in the Risks section. Severity is M when a worker following the spec top-down reads mechanically-incorrect text in a load-bearing section; L when the inaccuracy is in a fallback/risk-tracking section that a worker may consult but does not act on.

## M1 — rev4 L3 propagation gap: Decision 8 and Risks #3 still carry the stale `SystemExit`-wrapping wording

Rev4 L3 corrected [Decision 5 failure mode 3](spec-018-export_schema-0_0_7.md#decision-5--commanderror-for-three-failure-modes) (line 432-442) and the [Test plan](spec-018-export_schema-0_0_7.md#test-plan) test (f) paragraph (line 606) to describe Django's `CommandParser.error()` raising `CommandError` **directly** (no `SystemExit` involved on the `call_command` path). Verified against [`.venv/lib/python3.10/site-packages/django/core/management/base.py`](.venv/lib/python3.10/site-packages/django/core/management/base.py) — that fix is mechanically correct.

But rev4 L3 missed two other sites that carry the same superseded "`SystemExit` → `CommandError` wrap" wording:

**Site 1 — [Decision 8](spec-018-export_schema-0_0_7.md#decision-8--tests-go-through-call_command-not-direct-handle) bullet at line 514:**

> `call_command` wraps `SystemExit` from argparse into `CommandError` for the missing-positional-argument case; the test plan asserts the `CommandError` shape, which only the wrapper produces.

This is the load-bearing justification for [Decision 8](spec-018-export_schema-0_0_7.md#decision-8--tests-go-through-call_command-not-direct-handle)'s `call_command`-only test rule. A worker reading Decision 8 to understand *why* `call_command` is required reads a mechanism that doesn't exist (`call_command` does not wrap `SystemExit`), then turns to Decision 5 which correctly describes `CommandParser.error()` raising directly — the two sections now disagree about *which Django code path the test exercises*. The conclusion (only `call_command` exercises the path) is right; the mechanism description is wrong.

**Site 2 — [Risks and open questions](spec-018-export_schema-0_0_7.md#risks-and-open-questions) #3 at line 662:**

> **`call_command` and `CommandError` wrapping for missing positional argument.** Preferred answer: `call_command` wraps argparse's `SystemExit(2)` into `CommandError`, and `pytest.raises(CommandError)` catches it. Fallback: if Django's wrapping changes (unlikely; the behavior has been stable since the `call_command` helper was introduced), the test catches the new exception type and re-asserts; no production code changes.

Both the bullet title ("`CommandError` wrapping") and the "preferred answer" body claim a wrapping that does not exist. The fallback paragraph compounds the issue — it tells a future maintainer to watch for "wrapping" behavior changes when the actual stability concern is whether `CommandParser.error()` keeps the `called_from_command_line` branch.

This is the same propagation pattern that prior reviews flagged in rev2 L1 (`docs/TREE.md:190` fragment), rev3 M1 (Doc-updates vs Slice 3 checklist mismatch), and rev3 L2 ([Borrowing posture](spec-018-export_schema-0_0_7.md#borrowing-posture) "two divergences" residue): a wording fix lands at the primary site but skips parallel references in adjacent sections. Per the rev3 M1 framing — "the Doc updates section is the implementer-facing checklist that Worker 0 copies into the build artifact and Worker 2 walks during the implementation pass; if the section is incomplete, a worker following it top-down ships the stale sentence intact even though the Slice 3 checklist and DoD say otherwise" — the rev3 M1 propagation pattern applies again: Worker 2 may read Decision 8 (to understand the load-bearing test invariant) or the Risks section (to plan for fallback breakage) without re-reading Decision 5, and would internalize the wrong mechanism.

**Fix.** Apply the rev4 L3 wording shift to both remaining sites.

Site 1 — replace [Decision 8](spec-018-export_schema-0_0_7.md#decision-8--tests-go-through-call_command-not-direct-handle) line 514:

```
- `call_command` wraps `SystemExit` from argparse into `CommandError` for the
  missing-positional-argument case; the test plan asserts the `CommandError`
  shape, which only the wrapper produces.
```

with:

```
- Django's `CommandParser.error()` (a subclass-override of
  `argparse.ArgumentParser.error`) raises `CommandError` **directly** when
  `called_from_command_line=False`, which is the default when `call_command`
  constructs the parser. A direct `Command().handle(...)` call skips
  argparse entirely (and therefore skips `CommandParser.error()`), so the
  missing-positional `CommandError` path is unreachable without
  `call_command`. See [Decision 5](#decision-5--commanderror-for-three-failure-modes)
  failure mode 3 for the verified-against-Django-source mechanism.
```

Site 2 — replace [Risks](spec-018-export_schema-0_0_7.md#risks-and-open-questions) #3 line 662:

```
- **`call_command` and `CommandError` wrapping for missing positional
  argument.** Preferred answer: `call_command` wraps argparse's
  `SystemExit(2)` into `CommandError`, and `pytest.raises(CommandError)`
  catches it. Fallback: if Django's wrapping changes (unlikely; the
  behavior has been stable since the `call_command` helper was
  introduced), the test catches the new exception type and re-asserts; no
  production code changes.
```

with:

```
- **`CommandParser.error()` raising `CommandError` for missing positional
  argument.** Preferred answer: `CommandParser.error()` raises
  `CommandError` directly on the `called_from_command_line=False` branch
  (the branch `call_command` constructs), so `pytest.raises(CommandError)`
  catches it without any `SystemExit` involvement. Fallback: if Django
  changes the override (unlikely; the behavior has been stable since the
  `CommandParser` subclass was introduced), the test catches the new
  exception type and re-asserts; no production code changes.
```

Both rewrites preserve the load-bearing conclusion (only `call_command` exercises the path; Decision 8 stands) while replacing the mechanically-incorrect description with rev4 L3's verified-against-Django-source mechanism. After the edits, every spec section that mentions the missing-positional path agrees on what Django actually does.

Worth pinning explicitly in a new rev5 revision-history bullet that the rev4 L3 propagation now covers four sites (Decision 5 failure mode 3, Test plan test (f), Decision 8 bullet, Risks #3), so future reviewers can verify the propagation in one pass.

## L1 — Risks #1 mis-describes `import_module_symbol`'s actual signature

[Risks](spec-018-export_schema-0_0_7.md#risks-and-open-questions) #1 at line 660 reads:

> **Strawberry's `import_module_symbol` signature stability.** Preferred answer: the symbol's signature `(name: str, *, default_symbol_name: str | None = None) -> Any` has been stable since strawberry-graphql 0.x ...

Verified against [`.venv/lib/python3.10/site-packages/strawberry/utils/importer.py:4-6`](.venv/lib/python3.10/site-packages/strawberry/utils/importer.py:4) — the actual signature is:

```python
def import_module_symbol(
    selector: str, default_symbol_name: str | None = None
) -> object:
```

Three differences from the spec's description:

1. The first positional parameter is named `selector`, not `name`. Cosmetic.
2. `default_symbol_name` is **positional-or-keyword** (no `*` separator before it); the spec's `*,` claim says it's keyword-only. The package's actual call site (`Decision 3`'s code block and [Decision 2](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape)'s `Method signatures` block) uses the keyword form anyway, so the functional impact is zero — but a worker reading Risks #1 and then verifying against the source will see the mismatch.
3. Return type is annotated `-> object`, not `-> Any`. Mostly cosmetic, but `object` and `Any` have different mypy semantics — a future maintainer who depends on the return being `Any` (for unrestricted attribute access on the resolved schema) may be surprised.

This is in the Risks-and-open-questions section, so the inaccuracy doesn't affect Slice 1/2 implementation — but the section's job is to anchor future-maintenance assumptions about Strawberry's contract, and "the documented signature matches the source" is one of those assumptions.

Fix: rephrase Risks #1's preferred-answer signature to:

> Preferred answer: the symbol's signature `(selector: str, default_symbol_name: str | None = None) -> object` has been stable since strawberry-graphql 0.x ...

— matching the verified source. The body of the Risks bullet (the fallback "if a future strawberry-graphql minor release renames or removes the symbol..." paragraph) stays unchanged; only the signature line needs editing.

Single site. No other propagation.

---

## Summary

Action items for rev5:

1. **M1** — apply rev4 L3's wording shift to two missed sites: [Decision 8](spec-018-export_schema-0_0_7.md#decision-8--tests-go-through-call_command-not-direct-handle) bullet at line 514 and [Risks](spec-018-export_schema-0_0_7.md#risks-and-open-questions) #3 at line 662. Pin the rev4 L3 propagation as covering four sites in the revision-history entry.
2. **L1** — fix the `import_module_symbol` signature in [Risks](spec-018-export_schema-0_0_7.md#risks-and-open-questions) #1 at line 660 to `(selector: str, default_symbol_name: str | None = None) -> object`.

Neither item blocks Slice 1 implementation (the TODO scaffolding I just laid down in `django_strawberry_framework/management/commands/export_schema.py` and the test scaffolds is correct against rev4's Decision 5 mechanism — Decision 8 and Risks #3 are advisory sections the worker reads for context, not pseudo-code sources). M1 is medium because a worker who consults Decision 8 to defend the `call_command`-only rule against a teammate would quote text that contradicts Decision 5; L1 is low because Risks #1 is fallback-planning context that the worker does not act on during Slice 1.

Verified against the repo on 2026-05-22; spec rev4 (working tree after the rev4 edits landed; no commit hash since rev4 has not been committed yet).
