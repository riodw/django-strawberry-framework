# DRY review: `django_strawberry_framework/routers.py`

Status: verified

ITEM_BASELINE: `f856464baa330b3ff56fb79c628a100098f6b6b6`

## System trace

`routers.py` owns exactly one responsibility: materialize `DjangoGraphQLProtocolRouter`, a
`channels.routing.ProtocolTypeRouter` subclass wiring Strawberry's Channels consumers onto both
HTTP and WebSocket with Django auth (`AuthMiddlewareStack`) and origin validation
(`AllowedHostsOriginValidator`) composed in - byte-compatible with upstream
`strawberry_django.routers.AuthGraphQLProtocolTypeRouter` (confirmed by reading
`~/projects/strawberry-django-main/strawberry_django/routers.py` side by side with
`_build_router_class`'s `__init__`: identical composition, identical constructor signature). Three
sub-responsibilities ride along with it:

- **The soft-`channels` guard** (`require_channels`, `_CHANNELS_INSTALL_HINT`) - a thin wrapper
  over the package's one raising optional-import primitive,
  `utils/imports.py::require_optional_module`.
- **Split present-but-broken-install errors** (`_CHANNELS_BROKEN_HINT` /
  `_STRAWBERRY_CHANNELS_BROKEN_HINT`) - naming which half of the two-package import boundary
  failed (`channels.*` vs. `strawberry.channels`) so a broken Strawberry install is never
  misreported as a missing-channels problem.
- **Lazy, memoizing materialization** - `_build_router_class` caches the built class in the module
  global `_ROUTER_CLASS`; the PEP 562 `__getattr__` resolves the one public name
  (`DjangoGraphQLProtocolRouter`) through it on first access, so `import
  django_strawberry_framework.routers` and `import django_strawberry_framework` both stay
  channels-free and the install-hint `ImportError` fires only at the consumer's own `from ...
  import DjangoGraphQLProtocolRouter` line.

Traced every caller, sibling implementation, and connected contract:

- **`utils/imports.py::require_optional_module`** is the single owner every soft-dependency guard
  in the package wraps: `require_channels()` here, `rest_framework/__init__.py::require_drf()`,
  and `middleware/debug_toolbar.py::require_debug_toolbar()`. Its own docstring already states the
  design decision this review would otherwise re-propose - see Verification.
- **`utils/permissions.py`** owns the request-adapter half of the Channels story (the
  `ChannelsRequestAdapter` wrapping Strawberry's Channels dict context so
  `request_from_info()` resolves `.user`/`.session`/`.scope` plus delegated attributes). `routers.py`
  never touches request resolution; it only wires the consumers that hand resolvers that context.
  No overlap - confirmed by reading `utils/permissions.py::_channels_scope` and the adapter class in
  full.
- **`tests/_soft_dependency.py`** is the single shared soft-dependency absence-simulation harness
  (`evicted_modules` / `simulated_absence`) that `tests/test_routers.py`,
  `tests/rest_framework/test_soft_dependency.py`, and `tests/middleware/test_debug_toolbar.py` all
  import - already consolidated (its own docstring names all three call sites and the
  `builtins.__import__`-block precedent it replaced). Verified all three still import it and no
  test file hand-rolls a competing eviction/restore block.
  `tests/test_keyset.py::test_cursor_crypto_is_a_soft_dependency` also uses it for the package's
  fourth soft dependency (`cryptography`), confirming the harness generalizes cleanly beyond the
  three it was built for.
  - `django_strawberry_framework/keyset.py` is the package's fourth soft-dependency call site
    (`cryptography`, via two inline `require_optional_module` calls in
    `_cursor_crypto_types` rather than a named `require_cryptography()` wrapper). Read in full;
    out of scope for this file - `keyset.py` is a different plan item, and the stylistic
    inconsistency (named wrapper vs. inline calls) does not encode a shared rule this file owns.
- **Examples project.** `examples/fakeshop` ships no `asgi.py` (WSGI-only), so no live request can
  reach `DjangoGraphQLProtocolRouter` - confirmed by grep across `examples/`. This matches
  `docs/GLOSSARY.md`'s own justification for the package-tests placement of `tests/test_routers.py`
  ("A package-tests placement for new surface area must be justified as genuinely-unreachable-live
  ... the fakeshop example is WSGI-only"). No duplication to reconcile between a live-query test and
  a package test because there is no live path to test through.
- **Docs.** `docs/GLOSSARY.md`'s `DjangoGraphQLProtocolRouter` and `PEP 562 lazy export` entries and
  `docs/TREE.md`'s module-docstring-sourced one-liner all describe the exact behavior read from the
  source (constructor signature, split error hints, memoizing cache, `__all__` opting the submodule
  star-import into the guard). No drift found between code and doc.

## Verification

- **Searched for the soft-dependency-guard shape across the package** (`require_optional_module`,
  `require_drf`, `require_debug_toolbar`, `except ImportError as exc`). Found exactly four call
  sites of the shared primitive (`routers.py`, `rest_framework/__init__.py`,
  `middleware/debug_toolbar.py`, `keyset.py`) and confirmed all four already delegate to the one
  owner - this file's `require_channels()` is not a parallel reimplementation, it is the intended
  shape.
- **Considered consolidating the three install-hint STRINGS** (`_CHANNELS_INSTALL_HINT` /
  `_DRF_INSTALL_HINT` / `_DEBUG_TOOLBAR_INSTALL_HINT`) behind a shared template function (e.g.
  `format_install_hint(symbol, package, floor, label)`), since all three follow the identical
  English shape `"{Symbol} requires {package}, which is not installed. Install it with \`pip
  install '{package}{floor}'\` (the package's verified {label} floor)."`. Rejected: this exact
  design was already considered and explicitly turned down in the code itself -
  `utils/imports.py::require_optional_module`'s docstring states "There is deliberately NO
  `feature_label` parameter: the feature-specific text lives entirely in the caller's
  `install_hint` (the `require_drf()` shape), and hint strings stay single-sited at the feature
  owner." A templating helper would reintroduce exactly the `feature_label`-shaped parameter this
  primitive already rejected, and the three hints are not guaranteed to change together - each
  install-hint string is spec-owned by its own feature card (spec-039/041/042) and free to diverge
  in wording without any correctness impact on the other two (confirmed: `_STRAWBERRY_CHANNELS_BROKEN_HINT`
  already breaks the shared template by naming two floors, proving the shape is not even uniform
  today). Rejected.
- **Considered consolidating the PEP 562 module `__getattr__` pattern** shared with
  `django_strawberry_framework/__init__.py` (both end with `if <known name>: return <resolved
  value>` / `raise AttributeError(f"module {__name__!r} has no attribute {name!r}")`). Compared the
  two bodies in full: the root package's resolves seven DRF names through a `{name: (submodule,
  attr)}` dict, is explicitly NON-memoizing (so the absent-DRF test can re-hit the guard on repeat
  access without a stale binding), and returns an imported class it never constructs itself; this
  file's resolves exactly one name and IS memoizing (`_ROUTER_CLASS`), because it constructs an
  actual `ProtocolTypeRouter` subclass rather than importing one - `_build_router_class` is builder
  logic, not an import lookup, and rebuilding the class on every attribute access would produce a
  new class object each time (breaking `tests/test_routers.py`'s Test 6 identity assertion and any
  consumer that subclasses the router type once and expects stable `isinstance` checks against it).
  Genuinely different lifecycle contracts (import-vs-build, memoized-vs-not) driven by genuinely
  different responsibilities; a shared helper would need a `memoize: bool` flag to reconcile them -
  exactly what `DRY.md`'s ground rules warn against ("a helper that... needs mode flags to
  reconcile different rules makes the system less DRY"). Rejected.
- **Considered whether the two-tier "which half broke" error split**
  (`_CHANNELS_BROKEN_HINT` / `_STRAWBERRY_CHANNELS_BROKEN_HINT`) is a pattern duplicated, or that
  should be extracted, elsewhere. Grepped `except ImportError as exc` package-wide: the only other
  hits are `utils/imports.py::require_optional_module` itself (the one-hint primitive this file
  wraps, a different and simpler contract - one package, one hint) and an unrelated
  `types/finalizer.py` catch around `FieldSet` expansion. `rest_framework/__init__.py` and
  `middleware/debug_toolbar.py` each guard exactly one optional package with one hint and never
  need a second, half-specific message. This two-hint split is specific to `routers.py` because it
  is the only guard straddling two independently-installable packages (`channels` and
  `strawberry.channels`'s host, `strawberry-graphql`) behind one guard. No sibling to consolidate
  with; not a duplication.
- **Ran the read-only checks that matter for a soft-dependency-guard file**: confirmed
  `tests/test_routers.py` (18 tests, both channels-present and channels-absent/degraded states) and
  `tests/_soft_dependency.py` still exercise every branch named above; no test file was edited by
  this review since no source change was made.

## Opportunities

None — every candidate traced from this file either (a) is already single-sited at the correct
owner (`require_optional_module`), (b) was an already-considered-and-explicitly-rejected design in
the owner's own docstring (the install-hint templating), or (c) encodes a genuinely different
lifecycle/memoization contract that a shared helper would only obscure behind a mode flag (the two
module-level `__getattr__` implementations). The soft-dependency test harness
(`tests/_soft_dependency.py`) is already the single consolidated owner for all four of the
package's optional-dependency absence tests, `routers.py` included.

## Judgment

`routers.py` is a small, single-responsibility file whose one real cross-cutting concern (the
optional-import guard) was already consolidated onto `utils/imports.py::require_optional_module` by
a prior design pass (spec-041), with the alternative shapes this review would otherwise propose
(a shared hint template, a merged lazy-`__getattr__` helper) explicitly considered and rejected in
that same pass's own code comments. The item-scoped diff against baseline
(`f856464baa330b3ff56fb79c628a100098f6b6b6`) is empty - a well-proved zero-edit result. Ready for
Worker 2.

## Independent verification (Worker 2)

Re-traced from scratch rather than reviewing only the artifact's prose: read the complete
`routers.py`, `utils/imports.py`, `rest_framework/__init__.py`, `middleware/debug_toolbar.py`,
`keyset.py` (its `require_optional_module` call sites and `_cursor_crypto_types`), the module-level
`__getattr__` in the package root `__init__.py`, the instance-level `__getattr__` in `conf.py`,
`utils/permissions.py` (`ChannelsRequestAdapter` / `request_from_info`), `tests/_soft_dependency.py`,
`tests/test_routers.py` in full, `docs/GLOSSARY.md`'s `DjangoGraphQLProtocolRouter` / `PEP 562 lazy
export` entries, `docs/TREE.md`'s router line, and
`~/projects/strawberry-django-main/strawberry_django/routers.py` side by side with
`_build_router_class`'s inner class.

**Diff scope.** `git diff f856464baa330b3ff56fb79c628a100098f6b6b6 --
django_strawberry_framework/routers.py` is empty, and `git status --porcelain --
django_strawberry_framework/routers.py` shows no uncommitted changes either - confirmed
independently, matching the claimed zero-edit result exactly.

**Upstream parity re-check.** Read
`~/projects/strawberry-django-main/strawberry_django/routers.py::AuthGraphQLProtocolTypeRouter`
verbatim: constructor signature (`schema`, `django_application=None`, `url_pattern="^graphql"`) and
the full composition (`AuthMiddlewareStack(URLRouter(...))` for HTTP,
`AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(...)))` for WS, fallback appended after
the GraphQL route on the HTTP branch only) are byte-identical to `_build_router_class`'s inner
`DjangoGraphQLProtocolRouter`. Confirms the "byte-compatible with upstream" claim independently
rather than taking it on faith.

**Four-call-site re-check.** Independently grepped `require_optional_module` package-wide: exactly
four call sites (`routers.py::require_channels`, `rest_framework/__init__.py::require_drf`,
`middleware/debug_toolbar.py::require_debug_toolbar`, `keyset.py::_cursor_crypto_types`, the last one
inline rather than through a named wrapper). Read all four bodies in full - each is a thin,
non-memoizing pass-through carrying its own single `install_hint` string, none reimplements
`require_optional_module`'s try/except. Confirms `routers.py` is not a parallel reimplementation.

**Challenged rejected candidate 1: hint-string templating.** Read `require_optional_module`'s
docstring directly: it states verbatim "There is deliberately NO `feature_label` parameter" and
"hint strings stay single-sited at the feature owner" - a pre-existing design decision from the
primitive's own spec-041 origin, not an opinion invented by this review. Independently pulled all
four (not three) `*_INSTALL_HINT` bodies package-wide (`routers.py`, `rest_framework/__init__.py`,
`middleware/debug_toolbar.py`, and the previously-uncited `keyset.py::_CRYPTOGRAPHY_INSTALL_HINT`)
and confirmed all four follow the identical shape ("{Symbol} requires {package}, which is not
installed. Install it with `pip install '{package}{floor}'` (the package's verified {label}
floor)."). The artifact only named three; the fourth is out of scope for this file per the plan
(`keyset.py` is its own already-verified plan item) and its inclusion here would only strengthen a
template candidate, not weaken the rejection - so the omission does not change the judgment.
Separately, the artifact's one piece of supporting evidence for "the shape is not even uniform
today" cites `_STRAWBERRY_CHANNELS_BROKEN_HINT`, which is a present-but-**broken**-install hint, a
different category from the four present-but-**absent** hints being compared for templating; it
never claimed to follow the absence template, so that specific sentence conflates two hint families
and is not a valid uniformity counter-example. This does not change the outcome: the docstring's
explicit, pre-existing "no `feature_label` parameter" rejection is sufficient on its own, and each
hint string is independently spec-owned (spec-039/041/042, and keyset's own spec) and free to diverge
without a correctness dependency between them - exactly the "helper needing a mode flag" DRY.md warns
against, since a shared template would need a parameter for the very text the primitive already
excludes. Rejection upheld, with the artifact's supporting sentence noted as imprecise rather than
wrong-in-conclusion.

**Challenged rejected candidate 2: dual PEP 562 `__getattr__`.** Read `__init__.py::__getattr__` and
`routers.py::__getattr__` side by side, then proved the memoization divergence empirically rather
than by inspection alone: a scratch probe (`docs/dry/temp-tests/worker2-routers/`, deleted after use)
imported `django_strawberry_framework.routers`, accessed `DjangoGraphQLProtocolRouter` twice, and
confirmed `cls1 is cls2` and that `_ROUTER_CLASS` is populated as a module global after the first
access - `routers.py`'s `__getattr__` genuinely builds-and-caches. `__init__.py`'s body
(`getattr(import_module(submodule, __name__), attr)`) never writes to `globals()`, confirmed by
reading it - genuinely non-memoizing, by design (Decision 12's evict-and-re-hit contract). Also
independently found a THIRD `__getattr__` in the package (`conf.py::Settings.__getattr__`, an
*instance*-level attribute proxy over a settings mapping) that the artifact did not mention; read it
in full and confirmed it is not a PEP 562 module-level lazy-export at all (different binding target,
different responsibility - settings-key resolution vs. optional-dependency materialization), so its
absence from the artifact's comparison is correct, not a gap. The two module-level implementations
remain genuinely different lifecycle contracts; a shared helper would need a `memoize: bool` flag.
Rejection upheld.

**Test-suite re-check.** Read `tests/test_routers.py` in full (583 lines): confirmed all 18 named
test scenarios (including parametrized Test 9's three origin directions and Test 17's two
degraded-install halves) exercise every branch the system trace names - construction/composition,
real communicator execution, origin validation, memoized-class identity and subclassability,
channels-absent via the shared `simulated_absence`/`evicted_modules` harness, two-sided restore,
unrelated-attribute-miss passthrough, the split broken-install hints, and both the HTTP and
WebSocket request-context contract via `request_from_info`/`ChannelsRequestAdapter`. No stale test,
no orphaned import, no hand-rolled eviction block bypassing `tests/_soft_dependency.py`.

**Docs re-check.** `docs/GLOSSARY.md`'s `DjangoGraphQLProtocolRouter` and `PEP 562 lazy export`
entries and `docs/TREE.md`'s module-docstring-derived line match the source read directly; no drift.

**Missed-opportunity search.** Grepped the whole package for `ProtocolTypeRouter`,
`AuthMiddlewareStack`, `AllowedHostsOriginValidator` (only `routers.py` and, unrelatedly,
`utils/permissions.py`'s duck-typed adapter reference `channels`-shaped context by name, never the
classes) and for any second `_ROUTER_CLASS`-shaped memoizing builder or hand-rolled Channels wiring
in `examples/` or `tests/` - found none. Independently confirmed `examples/fakeshop` ships no
`asgi.py` (`rg --files examples -g 'asgi*.py'` empty), so the package-tests-only placement is
correctly justified and there is no live path this review is missing.

**Conclusion.** The zero-edit claim holds: the scoped diff is empty, both rejected candidates survive
independent re-derivation (one confirmed empirically), the four-call-site soft-dependency-guard
family and the shared absence-simulation test harness are correctly traced as already consolidated,
and no missed consolidation exists anywhere in the connected system. The one nit (an imprecise
supporting sentence for the hint-templating rejection, conflating an absence-hint template
comparison with a broken-hint example) does not change the judgment and does not warrant sending
this zero-edit item back for a documentation-only fix.

Status: verified.
