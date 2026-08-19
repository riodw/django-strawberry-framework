# Spec: [Django Trac #37064 hardening][glossary-django-trac-37064-hardening] + [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method]

Target release: `0.0.7` (per the [`KANBAN.md`][kanban] card `DONE-024-0.0.7`).
Status: shipped (`0.0.7`, 2026-05-27); archived. The spec is retained at this path as the durable record of the two-half defense against Django Trac #37064 and of the consumer-facing wrap helper. Its deliberative layer — the reconstructed derivation, every Decision's rejected alternatives, the change record, and every claim a Decision may no longer make — lives in [`spec-024-django_trac_37064_hardening-0_0_7-rationale.md`][spec-024-rationale].
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [Django Trac #37064 hardening][glossary-django-trac-37064-hardening], [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method], [Django `AppConfig`][glossary-django-appconfig]); [`KANBAN.md`][kanban] card `DONE-024-0.0.7`; sibling card spec [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] (owns the `AppConfig` shape and the `ready()` dispatch site this card's applier is called from); sibling card spec [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] (the multi-database cooperation contract whose consumers this bug reaches); joint-cut policy [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] ([Decision 10][spec-020-decision-10--joint-007-cut], reused in [Decision 11](#decision-11--joint-007-cut) here).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [Django Trac #37064 hardening][glossary-django-trac-37064-hardening] — the unwrap-time half: the package's replacement for `django.test.testcases.SimpleTestCase._remove_databases_failures`, installed automatically at app load.
- [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method] — the wrap-time half: the consumer-facing helper that declines to clobber Django's `_DatabaseFailure` wrapper.
- [Django `AppConfig`][glossary-django-appconfig] — the app-load hook the unwrap-time half is applied from; the `AppConfig` shape itself belongs to [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021].

The first two are this spec's project-specific terms; the companion [`docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-terms.csv`][spec-024-terms] binds each to the `docs/GLOSSARY.md` heading above, and `scripts/check_spec_glossary.py` validates that this spec links both anchors.

Project conventions to follow:

- [`AGENTS.md`][agents] — #"Test placement:" (package tests live under `tests/`; live HTTP tests under `examples/fakeshop/test_query/`); #"Test through real usage, prefer the example project" (with the unreachable-from-a-query fallback this card takes, see [Decision 10](#decision-10--coverage-lives-in-the-package-test-tree)); #"Add a settings key only when the feature that needs it lands" (the condition [Decision 6](#decision-6--apply_upstream_patches-is-the-escape-hatch) satisfies); #"Source refs in docs and code comments use symbol paths never line numbers".
- [`KANBAN.md`][kanban] — card-ID format and the `DONE-024-0.0.7` card body.
- [`docs/TREE.md`][tree] — rendered from module docstrings; the summary lines of all six of this card's surface modules are inputs to it — `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/apps.py`, `django_strawberry_framework/testing/_wrap.py`, `tests/test_django_patches.py`, `tests/testing/test_wrap.py`, and `tests/test_apps.py` — so a docstring edit to any of the six is followed by a regenerate.

## Slice checklist

Boxes are left unticked; the `Status:` line above is the source of truth for what shipped.

- [ ] Slice 1: the unwrap-time half — `django_strawberry_framework/_django_patches.py` with `apply()`, `_patched_remove_databases_failures`, and the ecosystem-precedent rationale docstring ([Decision 1](#decision-1--a-private-patch-module-per-dependency-applied-from-ready), [Decision 2](#decision-2--the-patch-installs-on-simpletestcase), [Decision 3](#decision-3--the-replacement-reimplements-the-loop-behind-one-guard)).
  - [ ] `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` calls the applier at app load.
  - [ ] `tests/test_django_patches.py` pins install-target, inheritance, unwrap, non-wrapper skip, the unpatched crash, idempotence, and self-healing re-install.
  - [ ] `tests/test_apps.py` permits `ready` on the `AppConfig` and pins its presence.
- [ ] Slice 2: fail-closed validation — `_validate_upstream_shape` in three tiers, the audited body set, and the read helper that covers both audited shapes ([Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers), [Decision 5](#decision-5--two-audited-upstream-bodies-discriminated-by-the-validated-source)).
- [ ] Slice 3: the `APPLY_UPSTREAM_PATCHES` gate in both its bool and per-dependency-mapping forms ([Decision 6](#decision-6--apply_upstream_patches-is-the-escape-hatch)).
- [ ] Slice 4: reload safety — the stamped owner/original attributes and `_captured_upstream_descriptor` ([Decision 7](#decision-7--idempotent-self-healing-and-reload-safe)).
- [ ] Slice 5: the wrap-time half — `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method`, exported from `django_strawberry_framework.testing`, with `tests/testing/test_wrap.py` ([Decision 8](#decision-8--the-wrap-time-half-degrades-where-the-unwrap-time-half-aborts), [Decision 9](#decision-9--the-helper-is-a-submodule-export-only)).
- [ ] Slice 6: doc updates — [`docs/GLOSSARY.md`][glossary] entries for both halves plus the `Public exports` line for the `testing` subpackage; the [`KANBAN.md`][kanban] `DONE-024-0.0.7` card; the [`CHANGELOG.md`][changelog] entry for `0.0.7` ([Doc updates](#doc-updates)).

## Problem statement

`django.test.testcases.SimpleTestCase._add_databases_failures` wraps every "disallowed" connection method on every non-permitted alias in a private `_DatabaseFailure` object at `setUpClass`. Its symmetric partner `_remove_databases_failures` unwraps them at `tearDownClass` by reading `method.wrapped` **unconditionally**.

If anything replaces `connection.<method>` between the two hooks — a consumer `setUp`, debug middleware, an instrumentation library, a mock — the attribute is no longer a `_DatabaseFailure` and teardown raises:

```
AttributeError: 'function' object has no attribute 'wrapped'
```

The test body itself passes; the crash is at class teardown and is unrecoverable. Django closed the ticket <https://code.djangoproject.com/ticket/37064> as `wontfix`, on the position that a third party which replaces Django's wrapper is responsible for restoring it.

This package's whole posture is that consumers do not add project-local boilerplate to make the package work, and multi-database cooperation ([`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023]) is a shipped contract whose users are exactly the ones Django wraps disallowed aliases for. So the package ships the fix itself.

## Current state

Both halves are shipped and installed by default:

- `django_strawberry_framework/_django_patches.py::apply` replaces `SimpleTestCase._remove_databases_failures`, called from `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`.
- `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` is exported from `django_strawberry_framework.testing`.

Neither upstream integration library ships a Trac #37064 patch; this is defensive hardening unique to this package.

## Goals

1. A consumer with `"django_strawberry_framework"` in `INSTALLED_APPS` never sees the Trac #37064 teardown crash, with no `conftest.py` workaround, no base test class, and no required settings key.
2. Well-behaved wrap sites have a cooperative helper that declines to clobber Django's wrapper in the first place, so the two guards compose.
3. The package never silently supersedes an upstream body it has not audited: dependency drift is a loud, targeted failure at app load with a named escape hatch, not a quietly dropped protection.
4. The patch survives a repeated `ready()`, a third-party revert of the class attribute, and an in-process `importlib.reload()` of the patch module.

## Non-goals

1. Restoration on the consumer's behalf. `safe_wrap_connection_method` handles the wrap step only.
2. Fixing the underlying multi-party monkey-patch design. The two guards mitigate the worst observable symptom at the two lifecycle sites this package can influence; they do not introduce an ordering protocol.
3. Upstreaming. Already attempted and closed `wontfix`.
4. Any consumer-facing pytest plugin or multi-database test-case base class.

## Borrowing posture

### From `strawberry-django` — no precedent to borrow

It ships no Trac #37064 patch and no cooperative connection-wrap helper.

### From `graphene-django` — no precedent to borrow

Same.

### Borrowed from `django-debug-toolbar`

- **The wrap-time `isinstance` check.** `debug_toolbar.panels.sql.tracking.wrap_cursor` refuses to install its cursor wrapper when it finds a `_DatabaseFailure` already in place. `safe_wrap_connection_method` is the same check exposed as a consumer API.
- **Not borrowed: the cache panel's owner-sentinel pattern.** Keeping a wrapper installed and toggling an owner sentinel works for a library that owns its own wrapper. This package does not own Django's `_DatabaseFailure`, so the pattern is unavailable for `_remove_databases_failures` itself. It remains the right shape for any future package-owned connection instrumentation.

### Explicitly do not borrow

Widening `TransactionTestCase.databases` / `TestCase.databases` to `"__all__"` in a repo-root `conftest.py`. That suppresses the wrapping rather than hardening the unwrap, and it is project-local boilerplate every consumer would have to copy.

## User-facing API

One public symbol, at the `django_strawberry_framework.testing` submodule path:

```python
def safe_wrap_connection_method(
    connection: BaseDatabaseWrapper,
    method_name: str,
    wrapper: Callable[..., Any],
) -> bool: ...
```

Worked consumer shape, from the helper's own docstring:

```python
from django.db import connections
from django.test import TransactionTestCase
from django_strawberry_framework.testing import safe_wrap_connection_method


class _MyTest(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self._connection = connections["default"]
        self._original_cursor = self._connection.cursor

        def my_wrapped_cursor(*args, **kwargs):
            return self._original_cursor(*args, **kwargs)

        self._wrapped = safe_wrap_connection_method(
            self._connection, "cursor", my_wrapped_cursor,
        )

    def tearDown(self):
        if self._wrapped:
            self._connection.cursor = self._original_cursor
        super().tearDown()
```

The unwrap-time half has no consumer-facing API. Its `apply()` carries no leading underscore only so the package's own regression tests can drive the apply-and-revert cycle without a second `AppConfig`.

### Error shapes

- `TypeError` — `safe_wrap_connection_method` received a non-callable `wrapper`. The message names the function and the condition and does **not** interpolate the object ([Decision 8](#decision-8--the-wrap-time-half-degrades-where-the-unwrap-time-half-aborts)).
- `RuntimeError` — `apply()` found upstream outside the shape it supersedes. Every such message names the `APPLY_UPSTREAM_PATCHES = {"django": False}` escape hatch ([Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers)).
- `ConfigurationError` — `APPLY_UPSTREAM_PATCHES` is configured in a shape that is neither a `bool` nor a `Mapping[str, bool]` over the known dependency names ([Decision 6](#decision-6--apply_upstream_patches-is-the-escape-hatch)).

## Architectural decisions

### Decision 1 — A private patch module per dependency, applied from ready()

The Django patch lives in its own private module, `django_strawberry_framework/_django_patches.py`, not inlined in `apps.py`. The leading underscore is the signal: consumers never import it; the patch is a side effect of app loading.

The organizing rule is **one patch module per third-party dependency**, each with its own `apply()` and its own name in `django_strawberry_framework/conf.py #"UPSTREAM_PATCH_DEPENDENCIES = frozenset("` (`{"django", "strawberry", "cross_web"}`). A further Django bug lands as another function inside `_django_patches.py`; a bug in another dependency gets its own module.

`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` dispatches the three appliers in order — Django, Strawberry, `cross_web` — behind function-local imports, so importing `apps` outside a configured Django project pulls in no patch module. This card owns the Django applier only; the dispatch site and the `AppConfig` shape belong to [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021], and each patch module's own docstring is the single source of truth for what it hardens. `ready()` deliberately repeats none of that inventory.

Rationale companion — the derivation, the rejected inline-in-`apps.py` alternative, and this Decision's change record: [Decision 1][rationale-d1].

### Decision 2 — The patch installs on `SimpleTestCase`

`apply()` installs the replacement on `django.test.testcases.SimpleTestCase._remove_databases_failures` — the class where Django **defines** the method. `TransactionTestCase`, `TestCase`, and any direct `SimpleTestCase` subclass are covered through the MRO; a direct `SimpleTestCase` subclass with `TransactionTestCase` nowhere in its MRO is covered, and is pinned as such.

Pinned by `tests/test_django_patches.py::test_patch_is_installed_on_simple_test_case`, `…::test_patch_is_inherited_by_transaction_test_case`, `…::test_patch_is_inherited_by_test_case`, and `…::test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`.

Rationale companion — the rejected `TransactionTestCase` target and why it lost: [Decision 2][rationale-d2].

### Decision 3 — The replacement reimplements the loop behind one guard

`django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures` reproduces upstream's teardown loop with exactly one behavioural addition: an `isinstance(method, _DatabaseFailure)` test, expressed as `django_strawberry_framework/_django_patches.py::_is_database_failure`, before the `setattr(connection, name, method.wrapped)` step.

- When Django's wrapper is still in place the check passes and the method is unwrapped exactly as upstream does.
- When it has been replaced the check fails and the foreign replacement is left untouched. That mirrors Django's own contract that `_add_databases_failures` / `_remove_databases_failures` operate symmetrically on the methods **they** wrapped; the patch declines to crash on a method the pair never owned.

The `(name, operation)` pair list is not read inline. It is read through `django_strawberry_framework/_django_patches.py::_disallowed_connection_methods`, so one replacement body covers both audited upstream shapes ([Decision 5](#decision-5--two-audited-upstream-bodies-discriminated-by-the-validated-source)).

Because the replacement **reimplements** upstream's whole loop rather than wrapping and delegating to it, an upstream body change does not flow through the patch the way it flows through the delegating sibling patch modules. That asymmetry is the reason the body pin in [Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers) exists at all, and it is implementation-relevant: a future contributor who removes the pin must first make the patch delegate.

Rationale companion — the rejected delegating-wrapper shape, and the claims this Decision may no longer make: [Decision 3][rationale-d3].

### Decision 4 — Fail-closed upstream validation in three tiers

`apply()` is **fail-closed**. Before installing anything it calls `django_strawberry_framework/_django_patches.py::_validate_upstream_shape`, which returns the validated body source and otherwise raises `RuntimeError`:

1. **Private symbols exist.** `django.test.testcases._DatabaseFailure` is importable, and the captured `_remove_databases_failures` is a `classmethod` descriptor with a `__func__`.
2. **Call shape holds.** The function takes exactly one `POSITIONAL_OR_KEYWORD` parameter.
3. **Body is audited.** `textwrap.dedent(inspect.getsource(function))` is a member of `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`. Source that cannot be read at all — `OSError` or `TypeError` from `inspect.getsource`, e.g. a bytecode-only distribution — is treated as drift, not as an exemption: an unverifiable body must not be silently superseded.

A missing private `_DatabaseFailure` symbol therefore **raises at app load**; it does not degrade, log, or no-op. Module *import* is still protected — the symbol import is wrapped in `try/except ImportError` so `apply()` can report the precise unsupported shape rather than dying at import — but the app does not boot until the consumer opts out.

Every one of the three messages names the escape hatch, so the failure carries its own remedy. `django_strawberry_framework/_django_patches.py::_disallowed_connection_methods` carries a fourth, defence-in-depth `RuntimeError` for the impossible case of running with no validated body at all.

Pinned by `tests/test_django_patches.py::test_apply_fails_loudly_when_database_failure_symbol_missing`, `…::test_apply_fails_loudly_when_upstream_method_signature_changes`, `…::test_apply_fails_loudly_when_upstream_body_drifts`, `…::test_apply_fails_loudly_when_upstream_source_is_unavailable`, and `…::test_disallowed_methods_rejects_an_unvalidated_upstream_shape`.

Rationale companion — the reversed graceful-degradation stance, the two tests retired with it, and the claims this Decision may no longer make: [Decision 4][rationale-d4].

### Decision 5 — Two audited upstream bodies, discriminated by the validated source

`_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` holds exactly **two** verbatim dedented upstream bodies, together spanning the whole supported Django range:

| Constant | Where the pair list lives upstream | Django range |
|---|---|---|
| `_CLASS_ATTRIBUTE_REMOVE_DATABASES_FAILURES_SOURCE` | the `SimpleTestCase._disallowed_connection_methods` class attribute | `5.2.16` - `6.0.x` |
| `_CONNECTION_FEATURE_REMOVE_DATABASES_FAILURES_SOURCE` | `connection.features.disallowed_simple_test_case_connection_methods`, read per connection | `6.1` |

Both shapes resolve to the same four `(name, operation)` pairs.

**The discriminator is the validated body source, never `hasattr(cls, …)` and never a version number.** `_disallowed_connection_methods` compares the module-level `_validated_remove_databases_failures_source` — assigned by `apply()` from `_validate_upstream_shape`'s return — against the two named constants. Reading the legacy attribute off `cls` is **not** equivalent: a Django 6.1 subclass may still declare its own `_disallowed_connection_methods`, but upstream's `_add_databases_failures` ignores it and wraps the feature list, so cleanup must read that same feature list to stay symmetric. This is implementation-relevant, not commentary: the `hasattr` form looks more robust and is not.

**Widening the set is an audit, not a version bump.** A third body joins only after (a) its read path is reimplemented in `_disallowed_connection_methods`, and (b) Trac #37064's crash shape is re-confirmed against it. Adding the string alone is insufficient. The obligation is stated verbatim in the constant's own leading comment at `django_strawberry_framework/_django_patches.py #"WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP"`.

Set size and both read branches are asserted in-suite by `tests/test_django_patches.py::test_validation_accepts_every_audited_upstream_body_and_refuses_a_third`, `…::test_disallowed_methods_read_prefers_the_class_attribute_shape`, and `…::test_disallowed_methods_read_falls_back_to_the_connection_feature_flag`. Whichever Django is installed leaves the other branch unreachable, so both are additionally driven synthetically.

Rationale companion — the single-pin form this superseded, the discriminator that was documented as a feature and is now named a bug, and the cost the pin imposes: [Decision 5][rationale-d5].

### Decision 6 — `APPLY_UPSTREAM_PATCHES` is the escape hatch

The unwrap-time half — and only that half — is gated by `DJANGO_STRAWBERRY_FRAMEWORK["APPLY_UPSTREAM_PATCHES"]`, read through `django_strawberry_framework/conf.py::upstream_patches_enabled`. Default is on; the key is an **opt-out**, never the delivery mechanism. A consumer still gets the backstop from `INSTALLED_APPS` alone.

Two configured shapes are accepted:

- **`bool`** — the global toggle. `False` stops the package monkey-patching any upstream dependency at startup.
- **`Mapping[str, bool]`** keyed by `UPSTREAM_PATCH_DEPENDENCIES` (`{"django", "strawberry", "cross_web"}`) — per-dependency opt-out. `{"django": False}` disables this test-only patch while leaving the production request-hardening patches installed. Missing names default to `True`.

Any other shape raises `ConfigurationError`: a non-bool / non-mapping value (a `"false"` string is truthy and would silently *enable* the patches), a non-string mapping key, an unknown mapping name (a typo must not silently keep patching), or a non-bool mapping value. The whole mapping is validated on every read, not just the dependency being asked about, so a typo fails at the first gate regardless of which patch module reads first.

**The gate is `apply()`'s first statement, ahead of all validation.** That ordering is the contract, not an accident: it is what makes `{"django": False}` a working recovery path for a consumer who upgraded Django ahead of the package and is currently being refused at boot by [Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers). A gate placed after validation would be unreachable in exactly the situation it exists for.

Pinned by `tests/test_django_patches.py::test_apply_no_ops_when_toggle_disabled`, `…::test_apply_no_ops_when_django_dependency_opted_out`, and `…::test_django_dependency_opt_out_silences_drifted_pin_abort`.

Rationale companion — the original "no settings escape hatch" decision, the justification that collapsed, and the two steps by which the hatch arrived: [Decision 6][rationale-d6].

### Decision 7 — Idempotent, self-healing, and reload-safe

`apply()` decides whether to install from **actual state**, not from a first-call-wins flag. `django_strawberry_framework/_django_patches.py::_patch_is_installed` reads `SimpleTestCase.__dict__` and compares `__func__` identity against the replacement.

- Re-entrant calls — `ready()` fires more than once under some Django test runners — are no-ops.
- A third party that reverted the class attribute since the prior call gets the patch re-installed on the next `apply()`. The contract is idempotent **and** self-healing; a boolean flag delivers only the first half.

**Reload safety is part of the contract.** `importlib.reload()` re-executes the module while `SimpleTestCase` still points at the previous replacement, so a naive re-capture would read the package's own function as "the original" and turn the next `ready()` into a false upstream-drift abort. Two module-level constants name the attributes stamped onto `_patched_remove_databases_failures` — `_PATCH_OWNER_ATTRIBUTE` (`"_django_strawberry_framework_patch_owner"`) and `_PATCH_ORIGINAL_ATTRIBUTE` (`"_django_strawberry_framework_original"`) — and a third, `_PATCH_OWNER` (`"django_strawberry_framework._django_patches"`), is the owner **value**, not an attribute name. `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor` compares the owner attribute against that value and, on a match, returns the stored original descriptor; otherwise it returns what it found.

Pinned by `tests/test_django_patches.py::test_apply_is_idempotent`, `…::test_apply_reinstalls_when_class_attribute_reverted`, `…::test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict`, and `tests/test_apps.py::test_ready_reinstalls_patches_after_their_modules_reload`, which reloads each patch module twice so the contract holds for a reload of a reload.

Rationale companion — the retired first-call-wins flag and the promise its docstring made that its code did not keep: [Decision 7][rationale-d7].

### Decision 8 — The wrap-time half degrades where the unwrap-time half aborts

`safe_wrap_connection_method(connection, method_name, wrapper)` returns `True` when it installed `wrapper`, and `False` when Django's `_DatabaseFailure` was already at the named attribute and the wrap was declined (the connection method is left untouched). It raises `TypeError` when `wrapper` is not callable — validated at the wrap site so a typo (passing `connection.cursor()`, the cursor object, instead of a callable) surfaces there rather than as a delayed failure deep in Django's ORM machinery. The `TypeError` message does **not** interpolate `wrapper`: the object is consumer-supplied and a hostile or broken `__repr__` would replace the intended `TypeError` with whatever the repr raises.

**The asymmetry with `apply()` is deliberate.** When the private `_DatabaseFailure` symbol is absent, `apply()` raises ([Decision 4](#decision-4--fail-closed-upstream-validation-in-three-tiers)) but the helper **installs and returns `True`**. Both halves share the same `_is_database_failure` predicate, and the helper degrades to "no Django wrapper is present, so the slot is free" rather than making the public `django_strawberry_framework.testing` import crash. A public import that dies on a private-symbol move is a worse failure than a wrap that proceeds; and the degraded path is only reachable with the Django patch opted out, since otherwise `ready()` has already refused to boot.

Restoration is the consumer's. The helper handles the wrap step only; the docstring carries the worked `setUp` / `tearDown` shape. The unwrap-time backstop makes omitting the restoration non-fatal, but restoring leaves a clean slot for the next `setUpClass` and for other libraries' wrap-time checks.

Pinned by `tests/testing/test_wrap.py::test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure`, `…::test_safe_wrap_connection_method_declines_when_database_failure_in_place`, `…::test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing` (the asymmetry), `…::test_safe_wrap_connection_method_works_on_arbitrary_method_names`, `…::test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth`, `…::test_safe_wrap_connection_method_raises_on_non_callable_wrapper`, and `…::test_safe_wrap_connection_method_keeps_type_error_boundary_for_hostile_repr`.

Rationale companion — why the fail-loud reversal deliberately stopped at the module boundary: [Decision 8][rationale-d8].

### Decision 9 — The helper is a submodule export only

`safe_wrap_connection_method` is exported from `django_strawberry_framework/testing/__init__.py` and is reachable at `django_strawberry_framework.testing`. It is **not** re-exported from the package root, and **no symbol from this card entered `django_strawberry_framework/__init__.py #"__all__ = ("`** — not at the ship and not since.

The public path is `django_strawberry_framework.testing`, never `django_strawberry_framework.test`. That is settled contract: a `test` subpackage shadows the stdlib name and collides with test-collection tooling. The package's own coverage for the helper lives at `tests/testing/test_wrap.py`.

Rationale companion — the rename that settled the path, and the reason a public surface is correct for this card at all: [Decision 9][rationale-d9].

### Decision 10 — Coverage lives in the package test tree

All coverage for both halves sits in `tests/` — `tests/test_django_patches.py`, `tests/testing/test_wrap.py`, `tests/test_apps.py` — and none in `examples/fakeshop/test_query/`.

That is the [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" fallback, taken deliberately: the failure is Django test-class setup/teardown behaviour and is **not reachable through a live `/graphql/` query**. The example project remains useful as fixtures, but this bug sits below the GraphQL API layer.

No `FAKESHOP_SHARDED=1` gate: the hardening protects every consumer, not only multi-database ones, so the tests run under the default single-database invocation. The sharded mode is the only one configuring more than one alias and is therefore a useful additional run of the same focused scope, not a separate suite.

Rationale companion — the rejected live-tier placement: [Decision 10][rationale-d10].

### Decision 11 — Joint `0.0.7` cut

The card ships in the joint `0.0.7` cut alongside its six siblings, under the policy [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut] establishes. No separate `0.0.8` cut for this card.

Rationale companion — the `0.0.8` alternative and why it lost: [Decision 11][rationale-d11].

## Implementation plan

One module, one helper, one dispatch line, three test modules:

1. `django_strawberry_framework/_django_patches.py` — the module docstring (bug inventory, ecosystem precedent, the settings paragraph, the surface-visibility note), the guarded `_DatabaseFailure` import, the three `_PATCH_*` constants, `_captured_upstream_descriptor`, the two audited body constants and the tuple over them, `_validate_upstream_shape`, `_is_database_failure`, `_disallowed_connection_methods`, `_patched_remove_databases_failures` plus the two `setattr` stamps, `_patch_is_installed`, and `apply()`.
2. `django_strawberry_framework/apps.py` — `ready()` calls the Django applier first of three, behind function-local imports.
3. `django_strawberry_framework/conf.py` — `APPLY_UPSTREAM_PATCHES_KEY`, `UPSTREAM_PATCH_DEPENDENCIES`, and `upstream_patches_enabled`.
4. `django_strawberry_framework/testing/_wrap.py` — `safe_wrap_connection_method`; re-exported from `django_strawberry_framework/testing/__init__.py`.
5. `tests/test_django_patches.py`, `tests/testing/test_wrap.py`, `tests/test_apps.py` — see [Test plan](#test-plan).

## Edge cases and constraints

- **The patch runs in production processes.** `ready()` fires outside tests too. `apply()` imports `django.test.testcases`, runs `inspect.signature` and `inspect.getsource` on one function, and compares two strings — once per `ready()`, at app load, never per request. The replaced method is only ever called from `tearDownClass`. What a production deployment must know is that this path is **fail-closed**: on an unaudited Django, `ready()` raises and the process does not start until `APPLY_UPSTREAM_PATCHES` says otherwise.
- **The body pin is exact source text.** Any upstream edit to `_remove_databases_failures` — a comment, a renamed local, a reflow, or an upstream fix of Trac #37064 itself — fails the membership test and aborts at `ready()`. That is the intended trade: a body the package has not audited must not be silently superseded. The escape hatch is the consumer's release valve while the audit is done.
- **`connections[…]` state is mutated by the tests and restored.** The suite assigns `connections["default"].cursor` / `.chunked_cursor` and, for the 6.1 shape, `connections[alias].features.disallowed_simple_test_case_connection_methods` across every alias, restoring in `try/finally`. The sentinel technique is the load-bearing part: `_DatabaseFailure(mock.sentinel.…)` for the happy path, a plain callable with no `.wrapped` for the bug path.
- **Only one audited branch executes per environment.** Whichever Django is installed makes the other body unreachable, so both read branches are covered synthetically and the floor run is what gives the `5.2.16` end of the claimed range an executed point.
- **`docs/TREE.md` is a downstream consumer** of the module summary lines of every one of this card's six surface modules — the three package modules `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/apps.py`, `django_strawberry_framework/testing/_wrap.py`, and the three test modules `tests/test_django_patches.py`, `tests/testing/test_wrap.py`, `tests/test_apps.py`. A docstring edit to any of the six is followed by a regenerate.

## Test plan

**This card owns 28 tests**, all in the package tree, all under the default single-database invocation: the whole of `tests/test_django_patches.py` (21) and the whole of `tests/testing/test_wrap.py` (7). No test in `tests/test_apps.py` is claimed here.

**The focused scope those three modules collect is wider — 36 tests** — because `tests/test_apps.py` runs whole, and all eight of its tests belong to [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021]. The two numbers answer different questions and are not interchangeable: 36 is the scope a run executes (it is what [Floor verification](#floor-verification) and [Definition of done](#definition-of-done) item 9 name as a run), and 28 is the population this card is responsible for (it is what every ownership claim here is stated against).

### `tests/test_django_patches.py` — 21 tests

- **Install and inheritance** — `test_patch_is_installed_on_simple_test_case`, `test_patch_is_inherited_by_transaction_test_case`, `test_patch_is_inherited_by_test_case`, `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`.
- **The fix proper** — `test_patched_remove_databases_failures_unwraps_a_real_wrapper` (a real `_DatabaseFailure` unwraps exactly as upstream does) and `test_patched_remove_databases_failures_skips_non_wrapper_methods` (a plain callable is left alone and does not raise).
- **The load-bearing negative** — `test_unpatched_remove_databases_failures_crashes_on_non_wrapper` reverts to the **live import-time capture** and asserts the crash still fires, having first asserted the captured descriptor's `__func__.__module__` is `django.test.testcases`. A hardcoded copy of some Django version's body could not deliver that signal: it would keep crashing regardless of what the installed Django ships, so it could never tell the maintainer the patch is retirable.
- **Idempotence, self-healing, reload** — `test_apply_is_idempotent`, `test_apply_reinstalls_when_class_attribute_reverted`, `test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict`.
- **Fail-closed validation** — `test_apply_fails_loudly_when_database_failure_symbol_missing`, `test_apply_fails_loudly_when_upstream_method_signature_changes`, `test_apply_fails_loudly_when_upstream_body_drifts`, `test_apply_fails_loudly_when_upstream_source_is_unavailable`.
- **The audited set and its read branches** — `test_validation_accepts_every_audited_upstream_body_and_refuses_a_third`, `test_disallowed_methods_read_prefers_the_class_attribute_shape`, `test_disallowed_methods_read_falls_back_to_the_connection_feature_flag`, `test_disallowed_methods_rejects_an_unvalidated_upstream_shape`.
- **The settings gate** — `test_apply_no_ops_when_toggle_disabled`, `test_apply_no_ops_when_django_dependency_opted_out`, `test_django_dependency_opt_out_silences_drifted_pin_abort`.

### `tests/testing/test_wrap.py` — 7 tests

The five contract clauses of [Decision 8](#decision-8--the-wrap-time-half-degrades-where-the-unwrap-time-half-aborts) — install into a free slot, decline on a `_DatabaseFailure`, install on private-symbol drift, work on an arbitrary method name, compose end-to-end with the unwrap-time patch — plus the two guarding the `TypeError` boundary (`…_raises_on_non_callable_wrapper`, `…_keeps_type_error_boundary_for_hostile_repr`).

### `tests/test_apps.py` — collected whole, owned by the sibling card

All eight of the module's tests belong to [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021]. Five pin the `AppConfig` shape — importability, subclass, `name` / `verbose_name`, registry pickup, and the consolidated forbidden-attribute negative. The other three pin `ready()`'s dispatch, and they are that card's too: each asserts a contract over **all three** patch appliers — `_django_patches`, `_strawberry_patches` and `_cross_web_patches` — while this card ships only the first, so the contract they pin is the dispatcher's, specified at that spec's `#"Decision 4"`. This card's commits authored those three tests because it was the first card to give `ready()` work to do; authoring is not ownership.

They are described here because this card depends on them: they are the only deterministic proof that `ready()` installs this card's applier at all. `ready` is permitted on the `AppConfig` (it is required on this class, not forbidden) and its presence is pinned by `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`. `test_ready_dispatches_all_three_patch_appliers_and_refires_safely` pins the dispatch deterministically — a per-module installed-at-collection assertion is masked by earlier direct `apply()` calls on the same worker, so a dropped dispatch line would otherwise pass the gate. `test_ready_reinstalls_patches_after_their_modules_reload` pins [Decision 7](#decision-7--idempotent-self-healing-and-reload-safe)'s reload contract.

### Floor verification

The subject is a Django integration seam pinned to exact upstream source text, so the focused scope re-runs at the supported floor — Django `5.2.16` on Python `3.10` with strawberry-graphql `0.316.0` — in an isolated venv. At the floor the class-attribute body is the validated one; in a newer environment the connection-feature body is. Without the floor run the `5.2.16` half of the audited set's claimed range is never executed by any real interpreter.

## Doc updates

- [`docs/GLOSSARY.md`][glossary] — entries for [Django Trac #37064 hardening][glossary-django-trac-37064-hardening] and [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method], plus the `Public exports` line for the `django_strawberry_framework.testing` subpackage.
- [`KANBAN.md`][kanban] — the `DONE-024-0.0.7` card, with this spec as its `SpecDoc` target.
- [`CHANGELOG.md`][changelog] — an entry for both halves under the `0.0.7` heading.
- [`docs/TREE.md`][tree] — regenerated whenever any of the three module summary lines changes.

## Risks and open questions

- **The pin will fire again.** An upstream release that edits `_remove_databases_failures` puts the installed body outside the audited set, `ready()` raises, and the package refuses to boot until the new body is audited. It has fired once already, on Django `6.1`, which removed `SimpleTestCase._disallowed_connection_methods` and moved the pairs onto the per-connection feature flag. That is the pin working as designed, and the resolution is an audit ([Decision 5](#decision-5--two-audited-upstream-bodies-discriminated-by-the-validated-source)) plus, for a consumer who cannot wait, the escape hatch ([Decision 6](#decision-6--apply_upstream_patches-is-the-escape-hatch)).
- **Retirement signal.** If upstream ever fixes Trac #37064, the body changes, the pin aborts, and the negative test stops crashing. Both are loud. The retirement decision is a maintainer's, not the patch's.
- **The wrap-time half is advisory.** The package cannot force third-party wrappers to use it, which is exactly why the unwrap-time half exists and is not optional.

## Out of scope (explicitly tracked elsewhere)

- A consumer-facing pytest plugin or multi-database test-case base class. The `django_strawberry_framework.testing` subpackage later grew a test-client family under a different card; that is not this card's surface.
- Patches for other Django `wontfix` bugs — one card each.
- Patches for other dependencies — their own modules, their own cards, their own names in `UPSTREAM_PATCH_DEPENDENCIES`.
- Upstreaming the patch.

## Definition of done

1. `django_strawberry_framework/_django_patches.py` ships `apply()`, `_patched_remove_databases_failures`, and the rationale docstring carrying the bug inventory and the ecosystem precedent.
2. `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` calls the Django applier at app load.
3. `apply()` is fail-closed across all three validation tiers and every message names the escape hatch.
4. `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` holds the two audited bodies, `_disallowed_connection_methods` discriminates on the validated source, and the widening rule is stated at the constant.
5. `APPLY_UPSTREAM_PATCHES` is honoured in both shapes, as `apply()`'s first statement, with `ConfigurationError` on any other shape.
6. `apply()` is idempotent, self-healing, and reload-safe.
7. `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method` ships with the documented return contract, the non-interpolating `TypeError`, and the deliberate private-symbol-drift asymmetry; it is exported from `django_strawberry_framework.testing`.
8. `django_strawberry_framework/__init__.py`'s `__all__` is unchanged by this card; no symbol from this work is re-exported from the package root.
9. This card's 28 tests — all of `tests/test_django_patches.py` and all of `tests/testing/test_wrap.py` — are green under the default invocation, under `FAKESHOP_SHARDED=1`, and at the supported floor, as is the 36-test focused scope those three modules collect whole (see [Test plan](#test-plan)).
10. No repo-root `conftest.py` workaround and no base test class is required of any consumer, at any point.
11. `uv run ruff format --check .` and `uv run ruff check .` both pass.
12. Docs updated per [Doc updates](#doc-updates); card `DONE-024-0.0.7` in `Done` at the joint `0.0.7` cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-django-appconfig]: ../GLOSSARY.md#django-appconfig
[glossary-django-trac-37064-hardening]: ../GLOSSARY.md#django-trac-37064-hardening
[glossary-safe-wrap-connection-method]: ../GLOSSARY.md#safe_wrap_connection_method
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[rationale-d1]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-1--a-private-patch-module-per-dependency-applied-from-ready
[rationale-d10]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-10--coverage-lives-in-the-package-test-tree
[rationale-d11]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-11--joint-007-cut
[rationale-d2]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-2--the-patch-installs-on-simpletestcase
[rationale-d3]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-3--the-replacement-reimplements-the-loop-behind-one-guard
[rationale-d4]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-4--fail-closed-upstream-validation-in-three-tiers
[rationale-d5]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-5--two-audited-upstream-bodies-discriminated-by-the-validated-source
[rationale-d6]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-6--apply_upstream_patches-is-the-escape-hatch
[rationale-d7]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-7--idempotent-self-healing-and-reload-safe
[rationale-d8]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-8--the-wrap-time-half-degrades-where-the-unwrap-time-half-aborts
[rationale-d9]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md#decision-9--the-helper-is-a-submodule-export-only
[spec-020]: spec-020-list_field-0_0_7.md
[spec-020-decision-10--joint-007-cut]: spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-021]: spec-021-apps-0_0_7.md
[spec-023]: spec-023-multi_db-0_0_7.md
[spec-024-rationale]: appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md
[spec-024-terms]: appx/spec-024-django_trac_37064_hardening-0_0_7-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
