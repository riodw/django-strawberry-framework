# Review feedback — `docs/spec-018-export_schema-0_0_7.md` (revision 3)

Reviewer pass against the rev3 spec, run after the rev2-feedback fixes landed. The spec is in good shape — all rev3 propagation cleanups (M1 / L1 / L2 / L3 / L4) verified intact against the repo, and every load-bearing claim about `pyproject.toml`, [`docs/TREE.md`](TREE.md), [`docs/README.md`](README.md), [`CHANGELOG.md`](../CHANGELOG.md), [`AGENTS.md`](../AGENTS.md), [`KANBAN.md`](../KANBAN.md), [`docs/GLOSSARY.md`](GLOSSARY.md), and the Strawberry / Django symbol surfaces was verified TRUE.

One medium-severity correction, four low-severity corrections, and one informational item below. Severity assigned by whether a worker following the spec top-down would ship a broken artifact (M) versus producing a correct artifact with mildly misleading commentary (L).

## M1 — `"type Branch"` fakeshop assertion names a type that does not exist

[Slice checklist](spec-018-export_schema-0_0_7.md#slice-checklist) line 62 and [Test plan](spec-018-export_schema-0_0_7.md#test-plan) → `examples/fakeshop/tests/test_commands.py` (extend) both pin the live-test assertion as `"type Branch"`. Verified against [examples/fakeshop/apps/library/schema.py:81](../examples/fakeshop/apps/library/schema.py:81): the `DjangoType` class is `BranchType`, and Strawberry emits the GraphQL type name from the Python class name unchanged — so the SDL contains `type BranchType {`, NOT `type Branch {`.

The substring assertion `"type Branch" in sdl` would still pass coincidentally (because `"type Branch"` is a prefix of `"type BranchType"`), but:

1. A reader scanning the spec assumes a GraphQL type literally named `Branch` exists in fakeshop — it does not (the only `Branch` in [examples/fakeshop/apps/library/](../examples/fakeshop/apps/library/) is the Django model at [models.py:32](../examples/fakeshop/apps/library/models.py:32), which Strawberry never exposes by that bare name).
2. A worker who tightens the assertion to an exact line match (`"type Branch {" in sdl` or a regex word-boundary match) would fail the test.
3. The substring `"type Branch"` would also match `BranchInput`, `BranchConnection`, etc. if such types ever land — losing the assertion's specificity.

Fix: change every `"type Branch"` reference in the spec to `"type BranchType"`. Three sites:

- [Slice checklist](spec-018-export_schema-0_0_7.md#slice-checklist) line 62 — `(e.g., "type Branch")` → `(e.g., "type BranchType")`.
- [Test plan](spec-018-export_schema-0_0_7.md#test-plan) `examples/fakeshop/tests/test_commands.py (extend)` paragraph (line 600) — `"type Branch"` → `"type BranchType"`.
- (No third site found in rev3; the assertion is referenced in exactly two places.)

Verified type names in fakeshop's library app for picking an alternative if `BranchType` later changes: `BranchType`, `ShelfType` (per [schema.py:57](../examples/fakeshop/apps/library/schema.py:57) docstring and [schema.py:81](../examples/fakeshop/apps/library/schema.py:81)).

## L1 — "Negative-shape test (one):" header contradicts the body that says "INTENTIONALLY OMITTED"

[Test plan](spec-018-export_schema-0_0_7.md#test-plan) lines 590-592 carry a header reading `Negative-shape test (one):` immediately followed by the single bullet's body which says the test is `INTENTIONALLY OMITTED for 0.0.7`. The header promises one test; the body delivers zero. A worker scanning section headers (or a future reviewer counting test bullets) would either author the omitted test or be confused by the count mismatch.

The body's rationale is correct and worth preserving (this card has no forbidden-key list to enforce, so a placeholder negative test would be noise). The only issue is the header wording.

Fix options (pick one):

- Rename the header to `Negative-shape test (none in 0.0.7):` — matches the body's intent and counts to zero.
- Rename to `Negative-shape test — deferred:` and keep the body explaining why.
- Move the entire paragraph into [Non-goals](spec-018-export_schema-0_0_7.md#non-goals) as `Forbidden-attributes negative test — no forbidden-key list exists yet; future cards add the test alongside their forbidden keys.`

The first option is the minimal-edit fix; the third is the cleanest structurally.

## L2 — Decision 2 `Method signatures` code block uses `...` as `handle` body alongside the docstring

[Decision 2](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape) `Method signatures` code block (lines 305-323) shows `handle` with both a docstring and a trailing `...`:

```python
def handle(self, *args: object, **options: object) -> None:
    """Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""
    ...
```

Both lines are statements; the `...` is redundant (the docstring alone satisfies the function-body requirement). More importantly, `...` is the stub-file (`.pyi`) idiom for "body intentionally elided" — a reader who only skims the code block could mistake this for the actual shipped body, then ship a `Command` whose `handle` does nothing.

The spec already names Decision 3, 4, 5 as the source of the real body in the prose around the block, but the code block itself is the most-scanned artifact in the spec, and the `...` line is the only thing under the docstring.

Fix: replace `...` with an explicit comment placeholder, e.g.:

```python
def handle(self, *args: object, **options: object) -> None:
    """Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path."""
    # Body per Decision 3 (symbol resolution) / Decision 4 (SDL output) / Decision 5 (errors).
```

`add_arguments` is fine as-is — it has a real body in the block.

## L3 — Decision 5 mis-describes how Django converts argparse failures to `CommandError`

[Decision 5](spec-018-export_schema-0_0_7.md#decision-5--commanderror-for-three-failure-modes) failure mode 3 (line 423) and the [Test plan](spec-018-export_schema-0_0_7.md#test-plan) test (f) paragraph (line 587) both describe the missing-positional path as: "Django wraps argparse's `SystemExit(2)` into `CommandError` only when invoked via `call_command(...)`."

The behavior is correct (the test passes with `pytest.raises(CommandError)`), but the mechanism described is wrong. Verified against Django 5.2's [`django.core.management.base.CommandParser.error`](.venv/lib/python3.10/site-packages/django/core/management/base.py): the conversion is NOT a wrapping of `SystemExit(2)` — `CommandParser` is a subclass of `argparse.ArgumentParser` whose `error()` method is overridden to raise `CommandError` **directly** when `called_from_command_line` is False (the default when invoked via `call_command`). The `SystemExit(2)` code path is the `called_from_command_line=True` branch, taken by `manage.py` from the shell.

The distinction matters because:

1. A worker who reads the current explanation and wants to verify the behavior by searching Django's source for `SystemExit` → `CommandError` conversion will not find it.
2. A future maintainer who wants to skip the `call_command` requirement might believe they can intercept `SystemExit` themselves — but the relevant code path never raises `SystemExit` in the first place when going through `call_command`.

Fix: rephrase failure mode 3's "wraps argparse's `SystemExit(2)` into `CommandError`" to "Django's `CommandParser.error()` (a subclass-override of `argparse.ArgumentParser.error`) raises `CommandError` directly when invoked via `call_command(...)` (the `called_from_command_line=False` branch); the `SystemExit(2)` branch is only taken when `manage.py` runs the command from a shell." Same edit to the [Test plan](spec-018-export_schema-0_0_7.md#test-plan) test (f) paragraph.

The load-bearing reason [Decision 8](spec-018-export_schema-0_0_7.md#decision-8--tests-go-through-call_command-not-direct-handle) requires `call_command` is preserved — a direct `Command().handle(...)` call skips argparse entirely (and therefore skips `CommandParser.error()`), so the missing-positional contract is unexercised.

## L4 — Definition-of-done items 8 and 13 have slight tension on the 100%-coverage gate

[Definition of done](spec-018-export_schema-0_0_7.md#definition-of-done) item 8 reads: "Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`)." Item 13 reads: "`uv run pytest --no-cov` passes (explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`, not this slice's; workers verify the suite passes, not that coverage stays at 100%)."

Item 8 names the 100% gate as a condition for "the card is complete." Item 13 disclaims that the worker enforces it. A worker reading top-down may conclude either:

(a) "Item 8 is a CI-enforced end-state and I don't need to run coverage locally" (matches Item 13); or
(b) "Item 8 says 100%, so I should run coverage locally to confirm before claiming done" (contradicts Item 13's `--no-cov` pin).

Both readings are defensible, but the spec should pin one. Recommended reading is (a) — `pytest --no-cov` is what the spec authorizes locally, and the 100% gate is verified by CI after the PR opens.

Fix: append to item 8 a clarifying clause: "(verified by CI, not by the worker locally; the worker's verification is item 13's `pytest --no-cov` suite-passing check)." OR reframe item 8 as "Package coverage is expected to stay at 100% under CI's `fail_under = 100` gate; if CI reports a coverage regression, the worker adds the missing test before merging."

Same posture as the parallel [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) (which the spec cites as the model for the gates section); the rev3 spec inherited the tension intact rather than resolving it.

## I1 — Informational: Decision 2's `: object` narrows on `*args` / `**options` are documentation-only

[Decision 2](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape) (lines 294, 320) pins `handle(self, *args: object, **options: object) -> None`. The spec correctly notes (line 294, line 333) that the `: object` narrows are NOT gate-forced — `ANN002` (missing `*args` annotation) and `ANN003` (missing `**kwargs` annotation) are globally ignored at [pyproject.toml:92-94](../pyproject.toml). So `*args, **options` (un-annotated, matching the upstream verbatim) would also pass `ruff check`.

This is a defensible stylistic choice — the narrows are nominally documentation-quality and make the type-checker behavior under `mypy --strict` more predictable. But the [Borrowing posture](spec-018-export_schema-0_0_7.md#borrowing-posture) "From strawberry-django — borrow the AppConfig shape verbatim" framing claims behavioral parity with the upstream, and the upstream uses bare `*args, **options`. The spec is internally consistent (the narrows are explicitly called out as additive), but a future maintainer rereading the [Borrowing posture](spec-018-export_schema-0_0_7.md#borrowing-posture) "two forced divergences" wording in isolation might delete the narrows as non-forced.

Two options:

- **Option A (keep the narrows):** Add one sentence to [Decision 2](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape)'s `Method signatures` sub-block: "The `: object` narrows on `*args` / `**options` are documentation-quality (ANN002 / ANN003 are globally ignored at `pyproject.toml:93-94`) but are pinned anyway for `mypy --strict`-friendliness; deleting them is acceptable if the upstream-verbatim shape is preferred."
- **Option B (drop the narrows):** Change every `*args: object, **options: object` reference to bare `*args, **options` and remove the [Decision 2](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape) discussion of `ANN002` / `ANN003` ignores. The Slice 1 [Slice checklist](spec-018-export_schema-0_0_7.md#slice-checklist) entry, the [Method signatures](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape) code block, and [DoD item 2](spec-018-export_schema-0_0_7.md#definition-of-done) would all simplify.

Option B is closer to the [Borrowing posture](spec-018-export_schema-0_0_7.md#borrowing-posture) "two categories of forced divergence" framing rev3 L2 just established (the narrows are a third, non-forced delta). Option A is the lowest-edit fix. No strong recommendation — flag for the author's call.

---

## Summary

Action items for rev4:

1. **M1** — fix `"type Branch"` → `"type BranchType"` in [Slice checklist](spec-018-export_schema-0_0_7.md#slice-checklist) line 62 and [Test plan](spec-018-export_schema-0_0_7.md#test-plan) line 600 (two sites).
2. **L1** — rename or restructure the contradictory `Negative-shape test (one):` header (lines 590-592).
3. **L2** — replace `...` with a comment placeholder in [Decision 2](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape)'s `handle` method signature (line 322).
4. **L3** — correct the argparse → `CommandError` mechanism wording in [Decision 5](spec-018-export_schema-0_0_7.md#decision-5--commanderror-for-three-failure-modes) failure mode 3 (line 423) and [Test plan](spec-018-export_schema-0_0_7.md#test-plan) test (f) (line 587).
5. **L4** — reconcile [DoD item 8](spec-018-export_schema-0_0_7.md#definition-of-done) and item 13 on the 100%-coverage gate.
6. **I1** — author's call: justify or drop the `: object` narrows on `*args` / `**options` in [Decision 2](spec-018-export_schema-0_0_7.md#decision-2--command-class-shape).

None of these block Slice 1 implementation if a worker started today — every behavioral pin in the spec is correct; the issues are wording, header, code-block, and documentation tension. M1 is the only item where a worker following the spec literally would emit an asymmetric artifact (an example name that doesn't match a real GraphQL type), and even there the substring match would coincidentally pass.

Verified against the repo on 2026-05-22; spec rev3 (commit `051a278`).
