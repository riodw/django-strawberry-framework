# PLAN — Django Trac #37064: `_remove_databases_failures` AttributeError

> **Status: TEMPORARY planning doc.** Pre-spec; written to scope the fix.
> The Phase 1 work below is **implemented**. Promote to a numbered
> `docs/spec-NNN-…-0_0_X.md` once the maintainer decides whether to ship
> as part of `0.0.7` (joint cut still open) or `0.0.8`. Delete this doc
> after the spec is in place.

## Context

Django Trac ticket — <https://code.djangoproject.com/ticket/37064> — filed and closed `wontfix`. Full reproducer at <https://github.com/riodw/django-remove_databases_failures-demo>.

### The bug, mechanically

`TestCase._remove_databases_failures()` (defined on `TransactionTestCase`; inherited by `TestCase`) walks every alias in `django.db.connections` at `tearDownClass` time and attempts to un-wrap the connection's "disallowed" methods:

```python
@classmethod
def _remove_databases_failures(cls):
    for alias in connections:
        if alias in cls.databases:
            continue
        connection = connections[alias]
        for name, _ in cls._disallowed_connection_methods:
            method = getattr(connection, name)
            setattr(connection, name, method.wrapped)  # ← BUG
```

Verified at `django.test.testcases.TransactionTestCase._remove_databases_failures` (Django 5.2.13). Same code path in Django 6.0.x.

The `method.wrapped` access assumes setup wrapped the method in a `_DatabaseFailure` and nothing between setUp and tearDown replaced it. If anything (test setUp, debug middleware, an optimizer extension under strictness, a monkey-patch) replaces `connection.<method>` with a plain callable in between, teardown crashes with:

```
AttributeError: 'function' object has no attribute 'wrapped'
```

The test method itself passes — the crash is at class teardown, which is **unrecoverable**.

### Why Django closed it

Django maintainers argue setup/teardown are symmetric and that third-party libraries replacing connection methods without restoring the originals are at fault. Their answer: those libraries should clean up after themselves.

### Why this package owns the fix

The whole point of `django-strawberry-framework` is that consumers should not have to add hacky boilerplate (a repo-root `conftest.py`, a base test case to inherit, etc.) to their own projects to make the package work. Multi-database cooperation (`DONE-019-0.0.7`) is a shipped contract; consumers building on it must not hit a Django test-framework crash whenever something replaces a connection method on a non-default alias. The package ships the fix unconditionally, applied at Django app-load time, so consumers get the protection for free by adding `"django_strawberry_framework"` to `INSTALLED_APPS`.

## The fix (implemented)

### `django_strawberry_framework/_django_patches.py` (new)

A private module that ships defensive patches to Django. Exports:

- `_patched_remove_databases_failures(cls)` — verbatim copy of Django's `_remove_databases_failures` body with an `isinstance(method, _DatabaseFailure)` guard added before the unwrap step. **This is exactly the patch Rio proposed in the upstream ticket.** When the method has been replaced with something that isn't a `_DatabaseFailure` wrapper, the patched method leaves it alone instead of crashing. When the wrapper is still in place, the patched method unwraps it exactly as upstream does.
- `apply()` — idempotent entry point that installs the patched method onto `TransactionTestCase` (and thereby onto `TestCase` via inheritance). Module-level `_PATCH_APPLIED` flag guards re-entry.

The module's leading-underscore name (`_django_patches`) signals it's a private internal surface — consumers don't import from it directly; the patch is applied as a side effect of Django's app-loading.

### `django_strawberry_framework/apps.py` (modified)

`DjangoStrawberryFrameworkConfig` now ships a `ready()` body that imports and calls `apply()`. `ready()` is Django's canonical one-time-setup hook; it fires once after all apps are loaded. Consumers who already had `"django_strawberry_framework"` in `INSTALLED_APPS` get the fix automatically with zero opt-in boilerplate.

### `tests/test_django_patches.py` (new) — 6 pytest items

Verifies the patch end-to-end (no `FAKESHOP_SHARDED=1` gate — the patch protects every consumer, not just multi-DB ones):

1. **`test_apply_is_idempotent`** — pins the idempotency contract.
2. **`test_patch_is_installed_on_transaction_test_case`** — `TransactionTestCase._remove_databases_failures.__func__` is `_patched_remove_databases_failures`.
3. **`test_patch_is_inherited_by_test_case`** — `TestCase` inherits the patched method via Django's class hierarchy.
4. **`test_patched_remove_databases_failures_unwraps_a_real_wrapper`** — happy path: when the method IS a `_DatabaseFailure`, the patched code unwraps it exactly as upstream does.
5. **`test_patched_remove_databases_failures_skips_non_wrapper_methods`** — the Trac #37064 fix proper: when the method has been replaced with a plain callable, the patched method leaves it alone and does NOT raise.
6. **`test_unpatched_remove_databases_failures_crashes_on_non_wrapper`** — the load-bearing negative test. Temporarily reverts `TransactionTestCase._remove_databases_failures` to a verbatim copy of Django's upstream body and asserts the bug DOES fire — pins that the bug is real at our Django pin (5.2.13) and the patch is load-bearing. A Django upgrade that quietly fixes the bug upstream would make this test fail, signalling that the package's patch can be retired.

### `tests/test_apps.py` (modified)

Removed `"ready"` from the forbidden-attributes assertion (it was inherited from spec-017's "no ready() body in 0.0.7" decision). Added `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches` — pins that `ready()` is present and callable, so a future refactor that removes it (and silently breaks the patch) fails loudly.

## Decisions made during implementation

- **Where the patch lives.** A new private module (`django_strawberry_framework/_django_patches.py`) rather than inlining in `apps.py`. The patch is ~30 lines of code with a 30-line rationale docstring; isolating it keeps `apps.py` short and gives future Django patches a natural home (e.g., if a Django 6.0 upgrade surfaces another `wontfix` bug we want to harden against, it lands in the same module). The underscore prefix marks it private.
- **Where the patch is applied.** `DjangoStrawberryFrameworkConfig.ready()`. Standard Django one-time-setup hook; fires once after app-loading. Idempotent in case `ready()` runs more than once under some test runners.
- **Whether to use the original cursor or a sentinel callable in tests.** The happy-path test uses `_DatabaseFailure(sentinel, ...)` and asserts the unwrap restores the sentinel; the bug-test uses a plain `_plain_cursor` callable with no `.wrapped` attribute. No real Django connection state is mutated for these tests.
- **Whether to ship a `DJANGO_STRAWBERRY_FRAMEWORK` settings escape hatch.** No — per `AGENTS.md` line 20 ("Add settings keys only when the feature that needs them lands"). If a consumer needs to disable the patch, they file a card. The patch is strictly defensive — it never makes Django's behaviour worse — so there's no foreseeable reason to opt out.
- **Whether to widen the `databases` allow-list (the previous conftest workaround).** **Rejected.** That was the wrong layer — it forced every consumer to add identical boilerplate to their own `conftest.py`. The package-level patch makes that boilerplate unnecessary. The conftest workaround has been deleted from the repo.

## Risks and open questions

- **Production cost.** `ready()` runs in production processes too, not just tests. The `apply()` function imports `django.test.testcases` and replaces a classmethod — both are no-op in production runtime (the patched method is never called outside `tearDownClass`). The one-time import cost is small (~10ms). Acceptable.
- **Class-attribute order under multi-Django-version support.** The patched method references `cls._disallowed_connection_methods`, which is what Django 5.2.13 uses. The upstream-ticket patch referenced `connection.features.disallowed_simple_test_case_connection_methods` (Django 6.0.x). When the package upgrades Django, the patch shape may need to evolve. The negative regression test pins the upstream method shape verbatim, so a Django upgrade that changes the iteration source will fail the negative test visibly and signal the patch needs updating.
- **`TestCase` vs `TransactionTestCase`.** `TestCase(TransactionTestCase)` inherits `_remove_databases_failures` — patching the base class covers both. Pinned by `test_patch_is_inherited_by_test_case`. If Django ever overrides the method on `TestCase` directly, our patch wouldn't reach the subclass; the inheritance test would fail loudly.
- **`SimpleTestCase` is NOT patched.** `_remove_databases_failures` is defined on `TransactionTestCase`, not `SimpleTestCase`. `SimpleTestCase` doesn't allow DB access at all, so the bug shape doesn't apply there. Verified at our pinned Django source.
- **Future patches in the same module.** `_django_patches.apply()` is the single entry point — additional patches land as more functions in the same module, each gated by their own `_<PATCH_NAME>_APPLIED` flag. The module's docstring lists implemented patches; consumers tracking what the package quietly fixes for them read that list.

## Definition of done

1. `django_strawberry_framework/_django_patches.py` exists with `apply()`, `_patched_remove_databases_failures`, and the rationale docstring. ✅
2. `django_strawberry_framework/apps.py` ships a `ready()` body that imports and calls `apply()`. ✅
3. `tests/test_django_patches.py` exists with the **6 regression tests** above; all pass under `uv run pytest --no-cov` (no `FAKESHOP_SHARDED=1` gate). ✅
4. `tests/test_apps.py` allows `ready` and pins its presence via `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`. ✅
5. The repo-root `conftest.py` workaround has been deleted. ✅
6. Full suite passes under both `uv run pytest --no-cov` and `FAKESHOP_SHARDED=1 uv run pytest --no-cov`. ✅ (787/3 + 789/2 at last verification.)
7. `uv run ruff format --check .` and `uv run ruff check .` both pass. ✅
8. `__all__` in `django_strawberry_framework/__init__.py` is unchanged. ✅ (The patch is a behaviour fix applied via AppConfig; no new public symbol.)
9. **Outstanding (maintainer decisions):**
   - `docs/GLOSSARY.md` — add an entry under the appropriate category (probably **Integration / tooling** or a new **Django compatibility** category) summarizing the Trac #37064 patch and pointing at `_django_patches.py`. Wording TBD.
   - `KANBAN.md` — add a `DONE-NNN-0.0.X` card describing the patch and linking to the Trac ticket.
   - `CHANGELOG.md` — append a bullet under `### Fixed` for the version this ships in. Wording TBD.
   - **Version target** — `0.0.7` joint cut (Decision 9 of `spec-019-multi_db-0_0_7.md`) or `0.0.8`? Maintainer's call.

## Out of scope for this plan

- Consumer-facing pytest plugin or `MultiDBTestCase` helper. The whole point of the package-level fix is that consumers don't need any of that.
- Patches for other Django `wontfix` bugs. Track each in its own card.
- Upstreaming the patch to Django. Already attempted; closed `wontfix`. We ship the fix unilaterally.

## Update: Consumer-facing helper now in scope (Phase 4)

The 019 spec deliberately shipped zero consumer-facing symbols (the multi-DB cooperation it pinned was already-existing behaviour). Bundling the Trac #37064 hardening with a consumer-facing wrap-time helper turns this branch into a real shippable feature instead of a behind-the-scenes patch.

**Landed**:

- `django_strawberry_framework/test/__init__.py` — new `test/` subpackage (pre-stages where `TestClient` / `GraphQLTestCase` will land at `0.0.12`).
- `django_strawberry_framework/test/_wrap.py` — `safe_wrap_connection_method(connection, method_name, wrapper) -> bool`. Returns `True` if installed; `False` if Django's `_DatabaseFailure` was in place and the wrap was declined. The wrap-time mirror of the unwrap-time backstop in `_django_patches`.
- `tests/test/__init__.py` + `tests/test/test_wrap.py` — 4 regression tests (install on free slot; decline on `_DatabaseFailure`; works on arbitrary method names; **end-to-end composition** with the unwrap-time patch).
- `docs/GLOSSARY.md` — new entries for `safe_wrap_connection_method` and `Trac #37064 hardening`, plus a `Public exports` list addition for the `test/` subpackage.
- `_django_patches.py` docstring updated to point at the helper (no longer "future card").

**Why a public surface here is correct, despite the package's general posture of zero public-export change**:

The 019 spec had Decision 2 ("no production code change") because the multi-DB cooperation was already in source — pinning it didn't need new symbols. Trac #37064 is different: the bug is in Django and ours is the first defensive layer, so the value-add IS a new behaviour. Shipping ONLY the AppConfig-applied unwrap patch protects every consumer but gives them no API to write defensive `setUp` code against. The helper makes the wrap-time half opt-in for consumers who care, while the unwrap-time half stays auto-applied for everyone.

**Test count after Phase 4**: 10 regression tests for the Trac #37064 area in total (6 unwrap-time in `tests/test_django_patches.py` + 4 wrap-time in `tests/test/test_wrap.py`), all under default single-DB mode (no `FAKESHOP_SHARDED=1` gate).
