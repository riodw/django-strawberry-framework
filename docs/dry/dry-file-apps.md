# DRY review: `django_strawberry_framework/apps.py`

Status: verified

## System trace

The file owns exactly two things: the package's identity in Django's app registry
(`DjangoStrawberryFrameworkConfig.name` / `.verbose_name`) and the app-load lifecycle hook
`apps.py::DjangoStrawberryFrameworkConfig.ready`, whose entire body is the deferred import and
invocation of three zero-arg appliers — `_django_patches.apply`, `_strawberry_patches.apply`,
`_cross_web_patches.apply`. It deliberately holds no other policy: gating lives inside each
`apply()` (`conf.py::upstream_patches_enabled` reading `APPLY_UPSTREAM_PATCHES`),
idempotence/self-healing in each module's `_patch_is_installed`, upstream-shape validation and
reload-recovery capture likewise per module. The dispatcher states this division itself: each
patch module's docstring is the source of truth for its bug inventory, and the function-local
imports keep `import django_strawberry_framework.apps` patch-free outside Django.

Consumers traced: Django resolves the config implicitly — fakeshop lists bare
`"django_strawberry_framework"` in `INSTALLED_APPS`
(`examples/fakeshop/config/settings.py`), and no `default_app_config` exists anywhere; direct
importers of the class are tests only (`tests/test_apps.py`; scratch under
`docs/review/temp-tests/apps/`). Tests pinning it: `tests/test_apps.py` — importability,
AppConfig subclass, name/verbose-name pins, forbidden attributes (Decisions 2/5/8: no label, no
`default_auto_field`, no `default`), `ready` presence, dispatch-plus-refire safety, and reload
reinstatement through the registered config. Prose media restating the contract:
`docs/GLOSSARY.md` ("Django AppConfig" and "upstream patches" entries) and the `docs/TREE.md`
one-liner. Sibling AppConfigs in `examples/fakeshop/apps/*/apps.py` (six) share only Django
convention; the lone sibling `ready()` body (`KanbanConfig`) imports signals — a different
lifecycle with nothing to mirror.

## Verification

Axis discharges:

1. **Cross-flavor policy mirroring** — searched `examples/` for `AppConfig|ready(` and the
   package for a second config class (only `django_strawberry_framework/apps.py` matches).
   Patch dispatch is a singleton surface with no per-flavor copies; the six example configs own
   unrelated lifecycles. Inapplicable on the target's real surface.
2. **Sync and async twins** — the target contains no await boundary: three synchronous
   zero-arg calls. The system's one genuine twin pair
   (`_strawberry_patches.py::_patched_sync_parse_multipart` /
   `_strawberry_patches.py::_patched_async_parse_multipart`) lives below the dispatcher,
   installed symmetrically by its owning module. Nothing on the target's surface pairs.
3. **Derived rather than repeated knowledge** — real candidate, examined and rejected (below):
   the triple {"django", "strawberry", "cross_web"} is enumerated twice in production —
   `conf.py#UPSTREAM_PATCH_DEPENDENCIES` (valid opt-out keys) and `apps.py`
   `ready()`'s dispatch (startup behavior) — with the `_<name>_patches` module-naming
   convention implicit between them. Grep confirms these are the only production enumerations.
4. **Inverse and round-trip pairs** — apply has no public inverse by design; uninstall exists
   only as test-side state restoration (`tests/test_apps.py` `_PATCHED_SLOTS` saved-descriptor
   table). That table mirrors what the modules patch but is restoration scaffolding, not a
   second owner of the rule: each module's `_patch_is_installed` remains the sole executable
   installed-state oracle, and a shared production "uninstall all" would be a test-only API.
   No encode/decode grammar splits across modules here.
5. **Contracts restated in another medium** — counted every medium carrying "ready dispatches
   three gated idempotent appliers": the dispatcher docstring, the three patch-module
   docstrings, `conf.py`'s toggle comment/docstring, four-plus GLOSSARY paragraphs, TREE
   one-liners, and the executable pins in `tests/test_apps.py`. Every non-test medium is prose
   pointing at code; the executable truths are single-sited (dispatch once, gate once in
   `conf.py::upstream_patches_enabled`, idempotence once per module). A behavior change moves
   documentation companions, never a competing implementation.

Single-edit-site counts:

- Posited: "register a Django system check in `ready()`" → **1** production site (the `ready`
  body). No other module or medium owns app-load setup for the package. Independence proved.
- Posited: "add a fourth upstream patch module" → **3** production sites (new module,
  `UPSTREAM_PATCH_DEPENDENCIES`, `ready` dispatch) plus tests/docs. This count drove the
  strongest candidate, rejected below.
- Posited: "retire the cross_web patch once upstream stops eager-decoding" → same co-varying
  trio, but each site moves for a different reason (module deleted; stale key removed; dispatch
  line removed) rather than sharing one statement of one rule.

Strongest rejected candidates:

- **Derive `ready()`'s dispatch from `UPSTREAM_PATCH_DEPENDENCIES`** (one inventory instead of
  two, e.g. `importlib.import_module(f"_{name}_patches").apply()` per frozenset member).
  Disproved on contract, not shape: the frozenset answers "which names may appear in the
  `APPLY_UPSTREAM_PATCHES` mapping"; dispatch answers "which appliers run at startup". Their
  equality is contingent (every shipped patch happens to want a kill switch), not essential —
  a future ungated patch would belong in dispatch but not in the opt-out vocabulary, so
  derivation would hard-code a false identity. Costs on top: frozenset iteration makes startup
  order nondeterministic unless the public-ish constant changes type; the naming convention
  becomes load-bearing yet unstated in any executable; startup drift surfaces as an opaque
  mid-loop `ModuleNotFoundError` instead of today's greppable three-line dispatch; and layering
  forbids the reverse derivation (`conf` cannot import the patch modules that import it — a
  shared registry leaf would add a third home for a three-element fact). The existing design
  already guards one drift direction loudly
  (`conf.py::upstream_patches_enabled` raises `ValueError` for unknown names, so a dispatched
  gate can never use an unlisted dependency); the silent direction (vocabulary name without a
  shipped/dispatched module) leaves an accepted-but-inert setting, inert by construction rather
  than wrong. A correspondence test could pin today's invariant, but pinning a contingent one
  as permanent is the false-invariant move this review rejects; revisit if the patch family
  grows past trivial size.
- **Shared stamp/capture scaffolding across the three sibling patch modules**
  (`_PATCH_OWNER_ATTRIBUTE` / `_PATCH_ORIGINAL_ATTRIBUTE` literals and the capture/mark helper
  pattern repeated per module). Verified not this file's duplication — `apps.py` shares none
  of it (it holds no stamps) — and verified the cross-module agreement of the attribute-name
  strings is not load-bearing today (each module reads only stamps bearing its own
  `_PATCH_OWNER` value). Ownership belongs to the three sibling file reviews and the folder
  integration pass for `django_strawberry_framework/`; recorded here only as a pointer.

## Opportunities

None — proved. The dispatcher's minimal-knowledge design is the correct ownership boundary:
every rule it touches has exactly one executable home elsewhere (gate in
`conf.py::upstream_patches_enabled`, install/idempotence/validation per patch module), and the
one above-one edit count found (adding or retiring a patched dependency) splits across sites
that answer different contracts — settings vocabulary versus startup behavior — whose current
alignment is contingent rather than identical, so merging them would encode a false invariant
while obscuring startup behavior. The independence proof is the system-check posited change
recounting to one forced site.

## Judgment

A forty-line file that succeeds by refusing to own anything. The tempting consolidation —
collapsing the two three-element inventories into one derived registry — was rejected on
contract analysis, not laziness: the two lists answer different questions, drift asymmetrically
by design, and their alignment is an artifact of every current patch wanting a kill switch.
Zero-edit result; the sibling-scaffolding pointer is handed to the folder pass. Pytest deferred
(no edits made; `ruff format`/`check` unnecessary without changes).

## Independent verification (Worker 2)

Scoped diff vs cycle baseline `bdf178b` is empty (`git diff bdf178b -- django_strawberry_framework/apps.py`);
the file is untouched this cycle. Independently re-traced and confirmed every load-bearing claim:
`ready()` is three function-local imports plus three zero-arg calls in the fixed order
django → strawberry → cross_web; each `apply()` self-gates as its first statement on
`conf.py::upstream_patches_enabled("<name>")` (`_django_patches.py:397`, `_strawberry_patches.py:788`,
`_cross_web_patches.py:342`) with capture/validation/idempotence entirely inside each module —
nothing of that lifecycle leaks into the dispatcher. Package-wide grep confirms `apps.py` is the
ONLY production dispatch site for the appliers (`testing/_wrap.py` imports `_is_database_failure`,
a helper predicate, not an applier); no `default_app_config` exists anywhere; fakeshop registers
the bare app name (`examples/fakeshop/config/settings.py:71`, implicit discovery) and exactly six
sibling AppConfigs exist, only Kanban's owning a `ready()` (signal imports, unrelated lifecycle).
`tests/test_apps.py` pins identity, forbidden attributes, dispatch-plus-refire through the
registered config, and reload reinstatement, as recorded.

Re-probed the strongest rejected candidate myself. Correspondence TODAY is exact 1:1 (three
frozenset names ↔ three modules ↔ three gate call sites), so derivation would be mechanically
clean — but it is not drift-safe-better, which was the bar: a frozenset name without a shipped
module is today an accepted-but-inert setting key (benign by construction), while derivation turns
that same state into a mid-startup `ModuleNotFoundError`; a new module without a frozenset entry
fails loud either way (today's `ValueError` from the gate names the fix). Derivation additionally
makes iteration order nondeterministic (frozenset) where the current order is deterministic and
prose-pinned, makes the `_<name>_patches` naming convention load-bearing yet unstated in any
executable, forbids the reverse direction by layering (`conf` cannot import modules that import
it), and hard-codes the contingent identity — plausible future ungated startup policy (the package
already ships view policy that deliberately does not ride the kill switch, per
`docs/GLOSSARY.md` #"neither depends on an upstream defect") would belong in dispatch but not in
the opt-out vocabulary. Rejection upheld. Also probed whether `ready()` duplicates lifecycle logic
belonging inside a patch module: it holds no gate, no idempotence check, no validation, and no
capture — none to move.

Matrix discharged against the target's real surface (re-checked, not trusted): axis 1 — one
AppConfig class in the package, no per-flavor copies (inapplicable with reason); axis 2 — no await
boundary in 43 lines (inapplicable); axis 3 — searched, yielded the real candidate above
(discharged); axis 4 — apply's only inverse is test-side restoration scaffolding
(`tests/test_apps.py` `_PATCHED_SLOTS`), preserved intentionally per DRY.md test-legibility rule,
each `_patch_is_installed` remaining the sole executable oracle (discharged); axis 5 — every
non-test medium is prose pointing at code, executable truths single-homed (discharged).

Count-of-one recounted with my own examples, agreeing with the artifact's: "connect a
`post_migrate` receiver at app load" forces **1** production site (the `ready` body — `conf.py`
deliberately wires its signal at import time instead, documented as not viable at app-load, so no
competing home exists); "flip patches from opt-out to opt-in" forces **0** sites here (default
lives in `conf.py::upstream_patches_enabled`, dispatcher untouched). Independence proved.

Verdict: zero-edit result stands. Status set to `verified`. Pytest remains deferred (no edits).
