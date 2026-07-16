# DRY review: `django_strawberry_framework/exceptions.py`

Status: verified

## System trace

`exceptions.py` owns the package's entire exception hierarchy and sits at the bottom of the
import graph (no Django, no Strawberry, no internal imports) so any layer can raise without a
circular. It defines exactly three public names (`__all__`):

- `DjangoStrawberryFrameworkError(Exception)` - the catch-all base. It keeps the ORIGINAL
  message args in `.args` (identity authoritative) and overrides `__str__` / `__repr__` to render
  safely at CALL TIME: each delegates to `super().__str__()` / `super().__repr__()` and, on ANY
  `BaseException`, substitutes `<unprintable ClassName>` (single arg) or a per-arg
  `_safe_arg_repr` tuple (multi arg); the rendered string is cached so a side-effecting arg is
  rendered at most once. (See Reconciliation - this supersedes an earlier construction-time
  `_sanitize_exc_arg` probe that this cycle replaced.)
- `ConfigurationError(DjangoStrawberryFrameworkError)` - the configuration-time failure family
  (Meta validation, settings reads, registry collisions, filter/order/mutation-set wiring).
- `OptimizerError(DjangoStrawberryFrameworkError)` - the optimizer-planning failure family
  (typed input guards, strictness-`"raise"` N+1 detection, window/fetch-mode contract violations).

`SyncMisuseError` is documented here (in `ConfigurationError`'s docstring) but actually defined in
`utils/querysets.py::SyncMisuseError(ConfigurationError, RuntimeError)`, re-exported at the package
root via `types/__init__.py` -> `django_strawberry_framework/__init__.py`. It is the only member of
the hierarchy in the public `__all__`; `ConfigurationError` / `OptimizerError` /
`DjangoStrawberryFrameworkError` are internal-but-importable (every raise site does
`from ..exceptions import ConfigurationError` / `OptimizerError`, never re-implements a class).

**Callers.** A grep across `django_strawberry_framework/` turns up ~30 modules importing
`ConfigurationError` and 4 importing `OptimizerError` (`optimizer/field_meta.py`,
`optimizer/plans.py`, `types/resolvers.py`, `utils/connections.py`), every one of them raising the
imported class directly - there is no second exception hierarchy, no per-subsystem
`FooConfigurationError` shadow class, and no module re-defining `ConfigurationError`/`OptimizerError`
locally. `utils/connections.py::UnwindowableConnection` is a plain internal `Exception`
(`noqa: N818`) explicitly scoped as an internal control-flow signal, not a surfaced framework
error - it deliberately does not join this hierarchy.

**Concurrent work note.** At dispatch, `exceptions.py` and (untracked) `tests/test_exceptions.py`
were already dirty. Diffing the current working tree against `ITEM_BASELINE`
(`c219e0d`) for both paths returns empty - the dirty content *is* the baseline snapshot, not a
divergence from it. Cross-referencing `docs/bug_hunt/bug_hunt-0_0_13.md` confirms this is the
already-verified bug-hunt fix for `exceptions.py` (hostile unprintable message args defeating
GraphQL-core's `located_error`, which calls `str(original_error)` and would otherwise replace the
typed exception with a raw `RuntimeError` on the wire). That fix - `_sanitize_exc_arg` plus its
`tests/test_exceptions.py` coverage - is concurrent, pre-existing, already-verified work belonging
to a different cycle. It is preserved untouched here.

## Verification

- `rg` for `class \w+.*(Error|Exception)` across `django_strawberry_framework/` returns exactly
  three hierarchy members (`DjangoStrawberryFrameworkError`, `ConfigurationError`,
  `OptimizerError`) plus `SyncMisuseError` (its declared multi-inherit subclass) and the
  intentionally-separate `UnwindowableConnection`. No shadow hierarchy exists to consolidate.
- `rg` for `raise \w*Error\(|raise \w*Exception\(` across the package confirms every
  `ConfigurationError`/`OptimizerError` raise site imports the class from `exceptions.py`; none
  redefines or wraps it with a local alias.
- Checked whether `_sanitize_exc_arg`'s "probe `str()` and `repr()`, substitute a placeholder on
  failure" pattern is duplicated anywhere else that also needs hostile-object tolerance. The
  closest candidate is `extensions/debug.py::_serialize_exception`, which calls bare
  `str(exception)` / `traceback.format_exception(...)` on an **arbitrary** caught `BaseException`
  (not necessarily a framework type) to build a debug payload row. **Rejected**: different
  contract and different failure mode. `_sanitize_exc_arg` exists so a framework exception's
  *identity* survives GraphQL-core's synchronous, unguarded `str(original_error)` call inside
  `located_error` - if that call raises, `located_error` replaces the typed
  `ConfigurationError`/`OptimizerError` with a bare `RuntimeError` on the wire, destroying
  `except ConfigurationError` catchability for the caller. `_serialize_exception` has no such
  identity-preservation requirement; its caller (`_collect_exceptions`, per the already-verified
  `extensions/debug.py` bug-hunt fix) is wrapped in a `try`/`except Exception` that logs and
  degrades the debug payload rather than losing exception identity on the wire. Reconciling these
  into one helper would couple a "keep typed identity through graphql-core" guarantee to a
  "best-effort debug logging" guarantee that tolerates the exact failure the first one forbids -
  the two must stay free to fail differently.
- Checked whether any production raise site passes a raw non-string object as a
  `ConfigurationError`/`OptimizerError` arg (the actual hostile-object exposure surface). Every
  production raise site formats its message into an f-string (`f"...{field!r}"`,
  `f"...{name!r}"`) before construction, so `_sanitize_exc_arg` only ever sees a `str` there - it
  guards the *possible*, not the *currently observed*, input (a `DjangoStrawberryFrameworkError`
  is public API; nothing stops a consumer or a future raise site from passing an object). Confirms
  the fix is scoped correctly at the shared base `__init__`, not at any individual raise site.
- Checked whether `ConfigurationError`'s and `OptimizerError`'s docstring "raise sites" catalogs
  duplicate the reasoning already written at each cited call site
  (`optimizer/field_meta.py::FieldMeta.from_django_field`, `types/resolvers.py`,
  `utils/connections.py::assert_window_fetch_mode` / `window_range_plan`,
  `optimizer/plans.py`). **Rejected as duplication**: the call-site docstrings explain *why that
  specific site* raises; the exception-class docstring is a system-wide index of *which sites
  raise this type*, an established repo idiom for this hierarchy, not two representations of one
  rule that must move in lockstep - removing either loses distinct, non-redundant information (a
  reader landing on the exception class has no other way to enumerate its raise sites; a reader at
  a raise site has no other way to learn the local justification).
- Confirmed no settings-driven or per-subsystem exception-hierarchy duplication: `conf.py`,
  `registry.py`, `permissions.py`, and every `*/sets.py` module raise the same imported
  `ConfigurationError`, never a local subclass.

## Opportunities

None - the exception hierarchy has exactly one owner (`exceptions.py`), every one of its ~30
importers uses it directly with no parallel representation, and the one apparent near-duplicate
(`extensions/debug.py::_serialize_exception`'s defensive `str()`/`traceback` serialization) solves
a materially different problem under a materially different failure contract, evidenced above.

## Judgment

`exceptions.py` is a clean, correctly-scoped foundation module: three classes plus the safe-render
overrides on the base, zero parallel implementations found anywhere in the package. The DRY
conclusion (single owner, no consolidation opportunity) is independent of the render mechanism and
stands. See Reconciliation for the rendering-contract change this cycle landed on top of the
earlier snapshot.

## Implementation (Worker 1)

No tracked changes made for this DRY item. `git diff c219e0deee78760e0818aa256fd3a2aa5b12bc52 --
django_strawberry_framework/exceptions.py tests/test_exceptions.py` (and no other paths were
touched) is empty, confirming the item-scoped diff is empty - the pre-existing dirty state on
these two paths is the concurrent bug-hunt fix captured *into* `ITEM_BASELINE` itself, not
something introduced or altered by this review. No `ruff format` / `ruff check --fix` run was
needed since nothing was edited.

## Independent verification (Worker 2)

Re-traced the target from scratch rather than reviewing only the artifact's citations.

**Zero-edit diff confirmed.** `git diff c219e0deee78760e0818aa256fd3a2aa5b12bc52 --
django_strawberry_framework/exceptions.py tests/test_exceptions.py` is empty in this
independent run too. Cross-checked `ITEM_BASELINE` itself: `git show c219e0d --
django_strawberry_framework/exceptions.py` is a merge commit whose diff already shows
`_sanitize_exc_arg` and the sanitizing `__init__` present - the baseline snapshot already
contains the concurrent bug-hunt fix, so there is nothing for this DRY item to have
introduced. `docs/bug_hunt/bug_hunt-0_0_13.md`'s `exceptions.py` entry (`Status: verified`,
"Hostile unprintable message args made GraphQL-core `located_error` replace typed
ConfigurationError/OptimizerError/SyncMisuseError with RuntimeError... Fix: ...
sanitizes args...") matches the working-tree content verbatim, confirming the concurrent
attribution rather than taking it on faith.

**Independent search for a missed consolidation opportunity.** Beyond the artifact's own
checks, I separately:

- Grepped the full package for every `class \w+.*(Error|Exception|Warning)` and for the
  string `sanitize`/`unprintable` (not just the ones the artifact already named). The only
  other `_sanitize_*`-named function in the package is
  `types/converters.py::_sanitize_member_name`, which coerces a Django enum CHOICE VALUE
  into a GraphQL-identifier-safe string (character replacement, keyword/reserved-word
  prefixing) - a name-shape transform on Django data, not an exception-arg printability
  guard. Shares nothing but the word "sanitize"; correctly out of scope and not worth the
  artifact's ink to reject explicitly.
- Confirmed `mutations/inputs.py::FieldError` / `utils/errors.py` (the GraphQL-wire
  validation-error envelope, a plain `@strawberry.type`, not an `Exception` subclass) is a
  different domain entirely (client-facing structured data vs. Python's raise/except
  machinery) and does not compete with the `exceptions.py` hierarchy for ownership.
- Independently grepped `raise ConfigurationError|raise OptimizerError` (33 raise sites
  across 26 files) and every `OptimizerError` import site (exactly the 4 files the artifact
  names: `optimizer/field_meta.py`, `optimizer/plans.py`, `types/resolvers.py`,
  `utils/connections.py`) - no shadow subclass, no locally redefined alias, matching the
  artifact's counts.
- Independently confirmed the `SyncMisuseError` re-export chain the artifact describes:
  `utils/querysets.py` defines it, `types/relay.py` re-exports it
  (`from ..utils.querysets import SyncMisuseError as SyncMisuseError`), `types/__init__.py`
  re-exports it again, and `django_strawberry_framework/__init__.py` re-exports it a third
  time into the public `__all__`. The artifact's summary ("re-exported at the package root
  via `types/__init__.py`") is accurate but skips the intermediate `types/relay.py` hop;
  noted here for completeness, not a defect - there is still exactly one definition.
- Found no fourth, fifth, or per-subsystem exception class anywhere under
  `django_strawberry_framework/` beyond the four already catalogued
  (`DjangoStrawberryFrameworkError`, `ConfigurationError`, `OptimizerError`,
  `SyncMisuseError`) plus the intentionally-separate `utils/connections.py::
  UnwindowableConnection`.

**Challenged the `_serialize_exception` vs `_sanitize_exc_arg` rejection directly** with a
scratch probe (`docs/dry/temp-tests/exceptions_w2/probe.py`, run and removed after use) to
try to disprove the "materially different failure contract" claim rather than accept the
prose:

1. Constructed `ConfigurationError(Hostile())` where `Hostile.__str__`/`__repr__` both
   raise. Confirmed `str(err)`, `repr(err)`, and formatting its traceback via
   `traceback.format_exception` all succeed cleanly (`str(err) == "<unprintable Hostile>"`)
   - i.e. `_sanitize_exc_arg`'s construction-time guard already makes every framework
     exception fully safe for `extensions/debug.py::_serialize_exception`'s bare
     `str()`/`traceback.format_exception()` calls, with zero changes needed to
     `debug.py`. This strengthens, not just repeats, the artifact's rejection: unifying the
     two helpers would be not only unnecessary but redundant for the framework-exception
     case the fix targets.
2. Constructed a plain `Exception` subclass (`ThirdPartyHostile`, never routed through
   `_sanitize_exc_arg`) whose `__str__` raises, and called
   `extensions.debug._serialize_exception` on it directly. It raised
   (`RuntimeError: third party str boom`), proving `_serialize_exception` genuinely has NO
   protection against a hostile non-framework exception - it depends entirely on its
   caller's outer `try/except Exception` in `_build_payload` to degrade the debug payload
   rather than corrupt the GraphQL response. This is the material difference the artifact
   claimed: `_sanitize_exc_arg` protects wire IDENTITY at construction (fail-safe, no
   `except` above it before `located_error` reads it), while `_serialize_exception` accepts
   an unguarded arbitrary `BaseException` and relies on its caller's degrade-and-log
   recovery. Coupling them would force one of the two correct-but-incompatible recovery
   policies onto the other's call site.

Both probes matched the artifact's reasoning with reproducible evidence rather than
plausible narrative, so the rejection stands independently verified, not merely
re-read.

**Conclusion.** No missed consolidation opportunity, no bypass. (The zero-edit / concurrent
framing above described the earlier snapshot; the rendering contract was subsequently revised
this cycle - see Reconciliation.)

## Reconciliation (final production contract)

The Worker 1 / Worker 2 narrative above describes the earlier construction-time
`_sanitize_exc_arg` probe (it ran `str()` and `repr()` at `__init__` and swapped each arg for a
placeholder in `.args`). That approach was **replaced** this cycle by call-time safe rendering,
for reasons the eager probe could not satisfy:

- it rendered `str` AND `repr` at construction and then again on the wire (repeated
  side-effecting rendering);
- it could not handle a DELAYED/STATEFUL arg whose `str()` succeeds at construction but raises
  later - the probe passed it through, and the wire `str()` call in `located_error` still broke;
- `except Exception` missed a dunder raising a `BaseException` subclass;
- it discarded the original argument identity from `.args`.

Final contract (identity authoritative): `DjangoStrawberryFrameworkError` keeps the caller's
original args in `.args` and overrides `__str__` / `__repr__` to delegate to `super()` and, on any
`BaseException`, return a `<unprintable ClassName>` (single arg) or per-arg `_safe_arg_repr` tuple
(multi arg), caching the result so each arg is rendered at most once. The wire-identity guarantee
(GraphQL-core `located_error` calling `str(original_error)` never raises, so the typed
`ConfigurationError` / `OptimizerError` / `SyncMisuseError` survives) is preserved and now also
holds for stateful and `BaseException`-raising args. `SyncMisuseError` (MRO:
`ConfigurationError -> DjangoStrawberryFrameworkError` before `RuntimeError`) inherits the base
overrides unchanged. The `_serialize_exception` non-consolidation rejection is unaffected: it is
still a different failure contract; only the framework-side mechanism moved from construction-time
to call-time.
