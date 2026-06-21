# Review: `django_strawberry_framework/testing/` (folder pass)

Status: verified

Folder pass over `django_strawberry_framework/testing/` covering the two
individually-`verified` siblings (`_wrap.py`, `relay.py`) plus the package
`__init__.py`. Cross-file checks: the `__init__.py` export surface, import
direction / circular-import risk, duplicated helpers, repeated literals, and
naming / error-handling / comment consistency. Both per-file artifacts
(`rev-testing___wrap.md`, `rev-testing__relay.md`) are `verified` and neither
forwarded a folder-level concern.

## DRY analysis

- None — the two in-scope modules are functionally unrelated (`_wrap.py` =
  cooperative connection-method wrapping for the Trac #37064 defense-in-depth;
  `relay.py` = public `global_id_for` / `decode_global_id` test helpers) and
  share no logic, no constant, no literal, and no cross-import, so there is
  nothing to consolidate *between* them. Each module is already the single-home
  shell over its own canonical internals: `_wrap.py` reuses the one shared
  `_django_patches.py::_is_database_failure` predicate (`_django_patches.py:134`,
  also consumed by the unwrap backstop at `:178`), and `relay.py` reuses the live
  encode path (`types/relay.py::encode_typename`), the shared gate constants
  (`types/base.py::_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` /
  `STRING_GLOBALID_STRATEGIES`), the verbatim `types/relay.py::decode_global_id`
  re-export, and the canonical `exceptions.ConfigurationError`. No folder-level
  helper would serve both files; any shared helper would have to live up in
  `_django_patches` / `types`, where it already does. Each per-file sibling
  recorded DRY-None for the same reason. Pulling a "shared testing util" out of
  two functions that touch disjoint subsystems would be a false consolidation.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Both modules are thin consumer-facing shells over
  already-single-sourced internals and introduce no folder-local duplication.
  `_wrap.py` imports the one shared `_is_database_failure` predicate
  (`_django_patches.py:134`) rather than re-spelling the
  `_DatabaseFailure is not None and isinstance(...)` test, so the wrap-time and
  unwrap-time halves of the Trac #37064 defense cannot drift. `relay.py` mints
  through `types/relay.py::encode_typename` (the exact slot the installed
  `resolve_typename` closure runs), reuses the `types/base.py` gate constants
  (`base.py:107,113,122`), reads the finalize-stamped
  `effective_globalid_strategy` rather than the raw setting (so it is
  consistent-by-construction with live emission), and re-exports
  `decode_global_id` verbatim from `types/relay.py` (`testing/relay.py:45`) — the
  same source the package-root `relay.py:65` consumer imports.
- **New helpers considered.** None at the folder level. The two files do not
  overlap in responsibility, so no shared `testing/`-internal helper or shared
  dataclass would serve both; the only helpers either file needs already exist
  one layer down (`_django_patches`, `types/`, `exceptions`). A folder helper
  here would manufacture coupling between two deliberately independent utilities.
- **Duplication risk in the folder.** None across siblings. The static overviews
  report 0 repeated string literals in `_wrap.py` and a single intra-file
  repeated literal in `relay.py` (`"global_id_for:"`, 4× — a per-raise
  `ConfigurationError` message prefix whose hoisting would hurt grep-ability of
  the raise sites, correctly not consolidated and already dispositioned in the
  per-file artifact). No literal appears in *both* files; the cross-sibling
  repeated-literal sweep over the three overviews (`__init__.py`, `_wrap.py`,
  `relay.py`) finds zero shared literals.

### Other positives

- **`__init__.py` export surface is correct and minimal.** `__all__ =
  ["safe_wrap_connection_method"]` (`testing/__init__.py:43`) exports exactly the
  one symbol that exists today, imported from `._wrap` at `:41`. The Relay
  helpers (`global_id_for` / `decode_global_id`) are deliberately **not**
  re-exported from the package init; their public entry is the dotted submodule
  path `django_strawberry_framework.testing.relay` (the card's DoD names the
  submodule path, and the docstring justifies it: keeping them out of `__init__`
  keeps `import django_strawberry_framework.testing` light, since `relay.py`'s
  `types`-package imports are paid only by suites that import the submodule). The
  `relay.py` module sets its own `__all__ = ["decode_global_id", "global_id_for"]`
  for the submodule path. No private symbol leaks out of either `__all__`.
- **Export intent matches real consumer usage.** The non-re-export is not just
  documented but exercised: every real consumer of the Relay helpers imports via
  the submodule path — `tests/mutations/test_fields.py:27`,
  `tests/mutations/test_resolvers.py:51`,
  `tests/mutations/test_permissions.py:39`, `tests/testing/test_relay.py:18`, and
  `examples/fakeshop/test_query/test_library_api.py:17` all do
  `from django_strawberry_framework.testing.relay import ...`, while the wrap
  helper is imported from the package init (`tests/testing/test_wrap.py:19`). The
  export surface and the consumer import paths agree.
- **Import direction is a clean one-way fan-out; zero circular-import risk.**
  `_wrap.py` and `relay.py` do not import each other; the only cross-mention is a
  docstring code example in `_wrap.py:89` (`from
  django_strawberry_framework.testing import safe_wrap_connection_method`), which
  is illustrative text, not an import edge. `__init__.py` imports only `_wrap`
  (`__init__.py:41`); it does not import `relay` (consistent with not
  re-exporting it). Dependencies flow strictly downward into package internals:
  `_wrap.py` → stdlib + `django.db.backends…BaseDatabaseWrapper` +
  `_django_patches`; `relay.py` → `strawberry.relay` + `exceptions` +
  `types/base` + `types/relay`. No package module imports
  `django_strawberry_framework.testing` (only consumer test suites do), so there
  is no back-edge from the core into `testing` and no `testing → testing`
  cross-edge. The "unrelated in function, minimal cross-file coupling"
  expectation from the spawn brief holds at source.
- **Naming / error-handling consistency across the pair.** Both module
  docstrings open with the same "consumer-facing test utilities" framing and
  cross-reference the same canonical sources (`_django_patches` for the Trac
  #37064 framing; the spec-032 Relay strategy system for the GlobalID contract).
  Naming is consistent with the package: public helpers carry no leading
  underscore and live in an `__all__`; the private predicate stays `_`-prefixed
  and is imported, not re-defined. The two files use distinct error vocabularies
  (`TypeError` at the `_wrap.py` callability guard; `ConfigurationError` at the
  `relay.py` mint gates) precisely because they guard distinct contracts — no
  drift, no inconsistent shaping for the same failure class.
- **GLOSSARY is accurate at the folder level.** `docs/GLOSSARY.md:52` describes
  `safe_wrap_connection_method` and `:53` describes the `global_id_for` /
  `decode_global_id` pair, including the load-bearing "NOT re-exported from the
  `testing` root, by design" clause — which matches `__init__.py:43`'s `__all__`
  exactly. The subpackage header (`GLOSSARY.md:50`) and the future-export
  forward-references (`TestClient` / `AsyncTestClient` / `GraphQLTestCase`,
  `GLOSSARY.md:168,629,1341`) match the `__init__.py` "Future exports" docstring
  (planned for `0.0.14`). No drift on any documented testing-surface symbol.

### Summary

`django_strawberry_framework/testing/` is a clean, well-bounded two-file
consumer test-helper surface joined only by a thin re-export `__init__.py`. The
two siblings — `_wrap.py` (the wrap-time half of the Trac #37064
defense-in-depth, a single 18-line `safe_wrap_connection_method`) and `relay.py`
(public `global_id_for` / `decode_global_id` GlobalID helpers) — are
deliberately independent: they share no code, constant, or literal with each
other, and each delegates to already-single-sourced machinery one layer down
(`_django_patches._is_database_failure`; `types/relay.encode_typename` +
`types/base` strategy constants + the verbatim `decode_global_id` re-export), so
folder-level DRY is correctly None. The export surface is correct and intentional
(only `safe_wrap_connection_method` re-exported; the Relay helpers public at the
submodule path by design, matching both GLOSSARY and real consumer imports);
import direction is a one-way fan-out into package internals with no intra-folder
coupling, no cycle, and no back-edge; and comment / naming / error-handling
conventions are consistent across the pair. Both in-scope siblings are
individually `verified` this cycle and were themselves genuine no-source-edit
cycles. The folder diff against the per-cycle baseline (`18e842e5`) and against
HEAD are both empty; the only dirty working-tree files are `docs/review/`,
`docs/dry/`, `docs/feedback2.md`, and `docs/spec-*` scratchpads (out of scope per
AGENTS.md #34). No High, Medium, or Low findings at folder scope; GLOSSARY
accurate. Zero edits to any tracked file → no-source-edit folder pass (shape #3 →
#5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged` (the COM812-vs-formatter
  advisory is pre-existing config noise, not a result of this cycle).
- `uv run ruff check --fix .` — `All checks passed!`

### Notes for Worker 3
- Folder pass with zero findings and zero edits. Both
  `git diff 18e842e56ede77c90bac5171b9f7e48229d718ea -- django_strawberry_framework/testing/`
  and `git diff HEAD -- django_strawberry_framework/testing/` are empty. The
  static helper ran on all three testing files at plan time (overviews exist
  under `docs/shadow/` for `__init__.py`, `_wrap.py`, `relay.py`). Shadow line
  numbers are not canonical; the artifact cites original source.
- Prior artifact's `__init__.py` +2 doc-bump finding (`0.0.12` → `0.0.14` in the
  "Future exports" docstring) is cumulative-in-HEAD this cycle — the live
  `__init__.py:28-29` already reads `0.0.14` and matches GLOSSARY. Not re-flagged
  (per worker-1 memory: re-check whether a prior forwarded item was since fixed
  before re-flagging).
- Export surface confirmed: `testing/__init__.py` `__all__ =
  ["safe_wrap_connection_method"]` only; `global_id_for` / `decode_global_id`
  intentionally NOT re-exported (submodule path is the public entry, exercised by
  real consumers in `tests/mutations/*`, `tests/testing/test_relay.py`, and
  `examples/fakeshop/test_query/test_library_api.py`).
- Import direction: `_wrap.py` and `relay.py` do not cross-import (the
  `_wrap.py:89` mention is a docstring example, not an edge); `__init__.py`
  imports only `_wrap`. No cycle; one-way fan-out into package internals; no
  back-edge from the package core into `testing`.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md:50,52,53` already match the
  source export surface and contracts verbatim (including the "NOT re-exported
  from the `testing` root, by design" clause and the `0.0.14` future-export
  rows).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits warranted. The `__init__.py` module docstring
(`__init__.py:1-39`) accurately lists the current export
(`safe_wrap_connection_method`), the deliberately-not-re-exported submodule-path
Relay helpers with the import-weight rationale, and the `0.0.14`-planned future
exports — and it is consistent with both sibling module docstrings and with
`docs/GLOSSARY.md`. No stale references, no obsolete TODOs (all three shadow
overviews report 0 TODO anchors). The two sibling files' comments/docstrings were
each accepted in their own verified cycles this same cycle.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. This folder pass makes no source change (empty
`git diff HEAD -- django_strawberry_framework/testing/`), so there is nothing to
record; and per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly
instructed") and the active plan (`docs/review/review-0_0_11.md`, silent on
changelog entries for review cycles), `CHANGELOG.md` is not touched.

---

## Verification (Worker 3)

Shape #5 no-source-edit folder pass over `django_strawberry_framework/testing/`.
Both in-scope siblings (`rev-testing___wrap.md`, `rev-testing__relay.md`) are
individually `verified` and `[x]` (review-0_0_11.md:129,130); neither forwarded a
folder-level concern.

### Logic verification outcome

No High / Medium / Low findings to disposition — all three buckets are `None` and
the artifact carries no forwarded sibling concern. The folder-level reasoning
verified at source:

- **Zero-edit proof (shape #5).** `git diff 18e842e5 -- django_strawberry_framework/testing/`
  empty; `git diff HEAD -- django_strawberry_framework/testing/` empty;
  `git diff --stat 18e842e5 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`
  empty (all exit 0, no output). Target absent from the owned-paths stat; no
  sibling attribution needed. Working-tree dirt is confined to `docs/` scratchpads
  (out of scope per AGENTS.md #34).
- **Export surface.** `testing/__init__.py:43` `__all__ = ["safe_wrap_connection_method"]`
  only, imported from `._wrap` (`:41`). The Relay helpers are NOT re-exported;
  `relay.py:47` sets its own `__all__ = ["decode_global_id", "global_id_for"]` at
  the submodule path. No private symbol leaks.
- **Cross-import / cycle.** `grep` for any `_wrap`↔`relay` edge returns nothing —
  `relay.py` imports only `strawberry.relay` + `exceptions` + `types/base` +
  `types/relay`; `_wrap.py` imports only stdlib + `BaseDatabaseWrapper` +
  `_django_patches`. The `_wrap.py:89` mention is docstring-only (inside the
  `.. code-block:: python` worked example, confirmed at source). One-way fan-out
  into package internals, no cycle, no back-edge.
- **No duplicated helpers.** The shared `_is_database_failure` predicate is single-
  sourced at `_django_patches.py:134`, consumed by the unwrap backstop (`:178`)
  and the wrap helper (`_wrap.py:27,144`) — 1 def / 2 consumers, no near-copy. The
  two testing modules share no logic, constant, or literal; DRY-None genuine.
- **Consumer import paths agree with the surface.** Relay helpers imported via the
  submodule path at `tests/mutations/test_fields.py:27`,
  `tests/mutations/test_resolvers.py:51`, `tests/mutations/test_permissions.py:39`,
  `tests/testing/test_relay.py:18`, `examples/fakeshop/test_query/test_library_api.py:17`;
  the wrap helper imported from the package init at `tests/testing/test_wrap.py:19`.

### DRY findings disposition

Folder-level DRY is correctly `None`. The two modules touch disjoint subsystems
(Trac #37064 connection wrapping vs GlobalID test helpers); any shared helper
would have to live one layer down where it already does (`_django_patches`,
`types/`, `exceptions`). No false consolidation. Each per-file sibling recorded
DRY-None for the same reason. Nothing forwarded to project pass.

### Temp test verification

None — no behavior suspicion to probe on a zero-finding folder pass.

### GLOSSARY (#4-vs-#5 gate)

GLOSSARY testing-surface prose is CORRECT vs live source, not merely untouched:
`GLOSSARY.md:50` subpackage header, `:52` `safe_wrap_connection_method`, `:53` the
`global_id_for` / `decode_global_id` pair including the load-bearing "NOT
re-exported from the `testing` root, by design" clause — matches `__init__.py:43`
exactly. Future-export forward-refs (`TestClient` / `AsyncTestClient` /
`GraphQLTestCase`, `:168,629,1341`) match the `__init__.py` "Future exports"
(`0.0.14`) docstring. No GLOSSARY-only fix in scope (would be disqualifying); none
present. `CHANGELOG.md` diff empty; "Not warranted" cites BOTH AGENTS.md and the
active plan's silence — accepted.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
testing/ folder-pass checklist box at `review-0_0_11.md:131`.
