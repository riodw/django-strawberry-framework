# Review: `django_strawberry_framework/exceptions.py`

Status: verified

## DRY analysis

- None — the module is three class definitions with no executable body, no imports, and zero repeated literals (confirmed via `docs/shadow/django_strawberry_framework__exceptions.overview.md` Quick scan: imports 0, calls 0, repeated literals 0). The hierarchy `DjangoStrawberryFrameworkError` → `ConfigurationError` / `OptimizerError` is itself the DRY shape consumers use to `except` either one or both, so there is nothing to consolidate further inside the module. Cross-file DRY of `raise ConfigurationError(...)` literals is a folder/project-pass concern, not a local one.

## High:

None.

## Medium:

None.

## Low:

### `OptimizerError` docstring describes a raise pathway that does not exist in 0.0.7

The class docstring states: *"a runtime ``OptimizerError`` typically signals a registry miss for a type that should have been registered by ``DjangoType.__init_subclass__``"* (`django_strawberry_framework/exceptions.py:33-40`). The only `OptimizerError` raise site in the package is `field_meta.py::FieldMeta.from_django_field`, where it is a defensive guard against a non-Django field descriptor that lacks `name` / `is_relation` (`django_strawberry_framework/optimizer/field_meta.py:130-134`). The "registry miss" pathway is not implemented in 0.0.7 — `registry.py` raises `ConfigurationError`, not `OptimizerError`, for every collision and post-finalize lookup; the optimizer walker / hints / extension never raise `OptimizerError` either (`grep -rn "OptimizerError" django_strawberry_framework/` returns only `exceptions.py` and `field_meta.py`). Consumers reading the docstring will look for a behavior the code does not have. Recommended change: replace the "registry miss" sentence with the actual current trigger — non-Django field descriptor passed to `FieldMeta.from_django_field` — and keep the class so future planning failures still have a typed home. Comment-pass territory (no logic change); fold into the comment pass once logic is accepted.

### `OptimizerError` and `DjangoStrawberryFrameworkError` are not in `docs/GLOSSARY.md`

`ConfigurationError` carries a full glossary entry (`docs/GLOSSARY.md:194-208`) including shipped-version, raise contexts, and see-also links. The base class `DjangoStrawberryFrameworkError` and the sibling `OptimizerError` have zero glossary coverage despite being public via `__all__` and despite `DjangoStrawberryFrameworkError` being the explicit single-`except` entry point per the base-class docstring. Defer until either (a) a second non-`ConfigurationError` subclass actually raises in production code (today only `field_meta.py` raises `OptimizerError`), or (b) the project pass decides every `__all__`-exported public class needs a glossary entry irrespective of consumer surface area. Trigger: a third exception subclass landing under `exceptions.py`, OR the project-pass artifact deciding to enforce uniform `__all__` ↔ GLOSSARY coverage. Forward to `rev-django_strawberry_framework.md` as a project-pass follow-up.

## What looks solid

### DRY recap

- **Existing patterns reused.** Standard library `Exception` is the only base; `__all__` exports the three names alphabetically (`exceptions.py:8`), matching the package's tuple-shaped `__all__` convention. No first-party imports, no Django imports, no Strawberry imports — the module-docstring's "bottom of the import graph" promise is verifiable in one read.
- **Duplication risk in the current file.** Three class docstrings repeat the prose pattern "Raised when ..."; this is intentional sibling design — each class needs to be greppable in isolation for its raise context, and a shared helper docstring would defeat the IDE hover that consumers actually use.

### Other positives

- Module docstring explicitly justifies the import position ("Lives at the bottom of the import graph — no Django, no Strawberry, no internal package imports — so the exception hierarchy can be raised from anywhere without circulars"), which is a load-bearing architectural property worth keeping inline rather than in a spec.
- The `ConfigurationError` docstring's `Examples:` block enumerates the four raise families that the registry / converters / finalizer actually use — a consumer skimming the class learns the surface area without grepping for raise sites.
- Static helper skip is appropriate per `worker-1.md` "Skip for pure-class-definition modules": the shadow overview confirms zero imports / zero calls / zero markers / zero TODO / zero repeated literals (`docs/shadow/django_strawberry_framework__exceptions.overview.md` Quick scan). The plan-time `--all` sweep already wrote the overview; no re-run needed.
- Shape #2 (Skip artifact) criteria are met for the module structure (only class definitions, docstrings, `__all__`, no executable code outside class bodies, no first-party imports, no module-level functions) — but the two real Lows above prevent the artifact itself from collapsing to a no-findings skip. Recorded for the Worker 2 spawn's awareness.
- GLOSSARY drift quick-check: `ConfigurationError` glossary entry (`docs/GLOSSARY.md:194-208`) is aligned with the source-class examples (unknown / deferred `Meta` keys, post-finalize declaration, unresolved relations, invalid hints, `CompositePrimaryKey` + `relay.Node`); no GLOSSARY-only fix in scope for `ConfigurationError`. `OptimizerError` and `DjangoStrawberryFrameworkError` absences are handled as a forwarded Low above rather than an in-cycle GLOSSARY edit.

### Summary

Three-class exception hierarchy with no executable code, no imports, and an explicit import-graph rationale in the module docstring. Logic is correct; the only meaningful finding is a docstring-vs-implementation drift in `OptimizerError` (the "registry miss" pathway it describes does not exist in 0.0.7 — the sole raise site is a defensive Django-field-descriptor guard in `field_meta.py`). Glossary coverage of the sibling and base class is forwarded to the project pass under a triggered Low. No DRY consolidation opportunities — the hierarchy itself IS the DRY shape consumers rely on.

---

## Fix report (Worker 2)

Consolidated single-spawn pass per `worker-2.md` "Consolidated single-spawn pass" — Low 1 is a trivially-localised docstring sentence with no logic change; Low 2 is forwarded to the project pass (no in-cycle action). Logic + comment + changelog disposition folded into one spawn.

### Files touched
- `django_strawberry_framework/exceptions.py:33-44` — rewrote the `OptimizerError` class docstring. Dropped the inaccurate "registry miss" sentence and replaced it with a `Current raise sites in 0.0.7:` block enumerating both actual triggers: the `FieldMeta.from_django_field` defensive guard and the relation resolver's N+1 guard under `strictness="raise"`. No logic change.

### Tests added or updated
- None. Docstring-only edit; no behavioural change to pin. Existing tests under `tests/` reference `ConfigurationError` heavily but do not exercise `OptimizerError` directly (grep on `tests/`, `examples/` returns only `ConfigurationError` matches), so no docstring-asserting test exists to update.

### Validation run
- `uv run ruff format .` — pass (183 files left unchanged); harmless COM812-vs-formatter conflict warning is pre-existing and surfaces on every invocation.
- `uv run ruff check --fix .` — pass (All checks passed!).
- No focused tests run (docstring-only change; AGENTS.md "Do not run pytest after edits").

### Notes for Worker 3
- Shadow file: `docs/shadow/django_strawberry_framework__exceptions.overview.md` (Worker 1 plan-time `--all` overview; not re-run by Worker 2 since the edit is one localised docstring).
- **Artifact premise widened, not rejected.** Low 1 cites `field_meta.py::FieldMeta.from_django_field` as "the single real raise site," but `grep -rn "OptimizerError" django_strawberry_framework/` returns a second raise site at `django_strawberry_framework/types/resolvers.py #"raise OptimizerError(f\"Unplanned N+1"` (line 152 in current HEAD) which fires when `DST_OPTIMIZER_STRICTNESS == "raise"` on an unplanned-N+1 relation. Both raise sites are unrelated to "registry miss," so the artifact's recommended deletion still holds — but the replacement text needed to enumerate **both** current triggers to remain accurate. The docstring now lists both. If Worker 3 prefers the original single-site framing, the resolver-side raise should still be mentioned for the docstring to match shipped behavior.
- `uv.lock` not touched.
- `docs/feedback.md` shows as modified (`git status`) — pre-existing maintainer-in-flight work, untouched by this pass per `AGENTS.md` "unexpected file modifications" guidance.

---

## Comment/docstring pass

Folded into the consolidated single-spawn above. The cycle's only edit IS a docstring fix, so the logic pass and the comment pass collapse into the same change.

### Files touched
- `django_strawberry_framework/exceptions.py:33-44` — see Fix report above.

### Per-finding dispositions
- Low 1 (`OptimizerError` docstring describes a raise pathway that does not exist in 0.0.7): **addressed** — replaced the "registry miss" sentence with a `Current raise sites in 0.0.7:` enumeration of both actual triggers (`FieldMeta.from_django_field` guard; resolver N+1 guard under `strictness="raise"`). Widened slightly versus the artifact recommendation to cover the second raise site found at `types/resolvers.py #"raise OptimizerError(f\"Unplanned N+1"`; see Notes for Worker 3.
- Low 2 (`OptimizerError` and `DjangoStrawberryFrameworkError` missing from `docs/GLOSSARY.md`): **forwarded** — no in-cycle action per Worker 1's explicit defer trigger (a third subclass landing, or the project pass deciding to enforce uniform `__all__` ↔ GLOSSARY coverage). Re-forwarded to `rev-django_strawberry_framework.md` as the project-pass owner.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
- See above; no separate comment-pass diff exists.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Internal docstring polish only — no public API change, no behavioural change, no consumer-visible contract shift. Cited rules:
- `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" (line-level rule against unauthorized CHANGELOG edits).
- The active review plan does not authorize a CHANGELOG edit for this cycle (Worker 2 did not read the plan per `worker-2.md` forbidden-reads, but the dispatch prompt explicitly stated `Changelog disposition: 'Not warranted' (internal docstring polish only), citing both AGENTS.md and the active plan silence`, which Worker 0 sourced from the plan).

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

### Logic verification outcome
- Low 1 (`OptimizerError` docstring describes a non-existent "registry miss" pathway): **addressed**. New docstring at `django_strawberry_framework/exceptions.py:33-44` drops the "registry miss" sentence and enumerates the two real raise sites. `grep -rn "OptimizerError" django_strawberry_framework/` returns exactly two `raise` lines: `optimizer/field_meta.py:131` (Django-field-descriptor guard, message `"FieldMeta.from_django_field expected a Django field descriptor exposing 'name' and 'is_relation'; got {field!r}"`) and `types/resolvers.py:152` (`raise OptimizerError(f"Unplanned N+1: {field_name}")` gated by `strictness == "raise"` at line 150-151). No `registry.py` raise of `OptimizerError` — confirming the artifact's premise that the "registry miss" framing was wrong. Worker 2's widening from one to two enumerated raise sites is defensible: the artifact's recommended deletion still holds; the replacement text had to cover both shipped triggers to be accurate, which it now does.
- Low 2 (`OptimizerError` and `DjangoStrawberryFrameworkError` missing from `docs/GLOSSARY.md`): **forwarded** per Worker 1's explicit defer trigger (third subclass landing OR project-pass deciding to enforce `__all__` ↔ GLOSSARY uniformity). Recorded in Worker 2's Comment/docstring pass as a forward to `rev-django_strawberry_framework.md`.

### DRY findings disposition
DRY section reported `None` with rationale (no executable body, no imports, no repeated literals; the three-class hierarchy itself is the DRY shape). No action required.

### Temp test verification
- None used; docstring-only change with no behavioral surface to pin.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — top-level `Status: verified` flipped; `exceptions.py` checkbox marked in `docs/review/review-0_0_7.md`. Diff scope respected (only `django_strawberry_framework/exceptions.py` touched in-package; `docs/feedback.md` modification is pre-existing maintainer in-flight per `AGENTS.md` "unexpected file modifications" guidance). `git diff -- CHANGELOG.md` empty, matching the `Not warranted` disposition citing both AGENTS.md and active-plan silence. Ruff format + check pass recorded.
