"""``DjangoListField`` — non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/spec-016-list_field-0_0_7.md``.
Target release: ``0.0.7``.

This module is a SCAFFOLD authored under Slice 1 of the spec. It currently
contains TODO markers and pseudo-code only — the real implementation lands
when Slice 1 (module + factory function) is executed against a verified
Slice 0 spike (see Slice checklist in the spec).

Why scaffolded ahead of implementation:

- Slice 0 (rev3 H1) is a verification spike that MUST succeed before any
  production code lands here. Until the spike confirms that
  ``DjangoListField(target_type)`` returning the value of
  ``strawberry.field(resolver=...)`` is picked up by ``@strawberry.type``
  class-attribute discovery, the factory-function shape below is provisional.
- Once the spike confirms the shape, fill in the TODOs in order:
  Slice 1 (this module's body), Slice 2 (constructor validation), Slice 3
  (behavior tests in ``tests/test_list_field.py``), Slice 4 (live HTTP
  coverage in ``examples/fakeshop``), Slice 5 (docs + promotion).
- If the spike fails, Decision 1's fallback (construct a ``StrawberryField``
  directly with explicit ``python_name`` / ``type_annotation``) is promoted
  and this module is reauthored.
"""

# TODO(spec-016, Slice 1 — Decision 2 pseudocode):
#   Replace the import block below with the production imports once Slice 0
#   confirms the ``from strawberry.types import Info`` path (rev5 H3). The
#   pseudo-code body keeps the imports inline as a reading aid; the final
#   module imports them at the top.
#
#       import inspect
#       from typing import Any, Callable
#
#       from django.db import models
#       from strawberry.types import Info  # rev4 H1: ``info`` MUST be annotated;
#                                          # rev5 H3: Slice 0 verifies the path.
#       from strawberry.utils.inspect import in_async_context  # rev3 M7,
#                                                              # verified at
#                                                              # ``types/relay.py:33``.
#
#       import strawberry
#
#       from .exceptions import ConfigurationError
#       from .types.relay import (
#           _apply_get_queryset_sync,
#           _apply_get_queryset_async,
#       )  # Decision 3 Option A — import from the existing helper site.


# TODO(spec-016, Slice 1 — Decision 1 mechanism + Decision 2 default resolver):
#   Implement ``DjangoListField`` as a factory function. Pseudo-code below
#   tracks the spec Decision 2 pseudo-code one-to-one. The ``# noqa: N802``
#   on the ``def`` line is intentional (rev5 L1 — PascalCase function name
#   for graphene-django parity; consumers write ``DjangoListField(BranchType)``
#   mirroring the upstream class-import shape).
#
#       def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity
#           target_type: type,
#           *,
#           resolver: Callable | None = None,
#           description: str | None = None,
#           deprecation_reason: str | None = None,
#           directives: tuple = (),
#       ):
#           # ----- Slice 2 — Validation (Decision 5) -----
#           # TODO(spec-016, Slice 2): raise ``ConfigurationError`` for each of:
#           #   * not a class                       → "DjangoListField requires a DjangoType class; got <repr>."
#           #   * not ``issubclass(arg, DjangoType)`` → "DjangoListField requires a DjangoType subclass; got <name>."
#           #   * missing ``__django_strawberry_definition__`` (rev3 M3 anchor
#           #     at ``types/base.py:245``) → "DjangoListField target <name> is not a registered DjangoType ..."
#           #   * ``resolver`` supplied but not callable → "DjangoListField resolver must be callable."
#           #
#           # Error message shape mirrors ``types/base.py:_format_unknown_fields_error``
#           # ("<Symbol> <constraint>; got <repr>.") for consistency.
#
#           # ----- Slice 1 — Post-processing helpers (Decision 2, rev5 M4) -----
#           # ``info`` and ``target_type`` are EXPLICIT parameters (rev5 M4 —
#           # closing over ``info`` at factory time would NameError; ``info``
#           # only exists per-call inside ``_default`` / ``_wrap``).
#           def _post_process_sync(target_type, result, info):
#               if isinstance(result, models.Manager):
#                   result = result.all()  # field-wrapper Manager → QuerySet coercion (rev4 M1).
#               if isinstance(result, models.QuerySet):
#                   return _apply_get_queryset_sync(target_type, result, info)
#               return result  # Python list / generator — pass through.
#
#           async def _post_process_async(target_type, result, info):
#               if isinstance(result, models.Manager):
#                   result = result.all()
#               if isinstance(result, models.QuerySet):
#                   return await _apply_get_queryset_async(target_type, result, info)
#               return result
#
#           # ----- Slice 1 — Default resolver vs consumer-resolver wrap -----
#           if resolver is None:
#               # Default body. ``in_async_context()`` is checked PER-CALL
#               # (Decision 2 async-detection asymmetry, rev5 H2) — the same
#               # factory output dispatches correctly under both
#               # ``schema.execute_sync(...)`` and ``await schema.execute(...)``.
#               # Pinned by ``test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution``
#               # (rev5 M3).
#               def _default(root: Any, info: Info):
#                   qs = target_type.__django_strawberry_definition__.model._default_manager.all()
#                   if in_async_context():
#                       async def _async_path():
#                           return await _apply_get_queryset_async(target_type, qs, info)
#                       return _async_path()
#                   return _apply_get_queryset_sync(target_type, qs, info)
#               wrapped = _default
#           else:
#               user_resolver = resolver
#               # Consumer-wrapper async detection commits PER-CONSTRUCTION
#               # (Decision 2 async-detection asymmetry, rev5 H2) — Strawberry
#               # inspects the resolver signature once at schema construction.
#               if inspect.iscoroutinefunction(user_resolver):
#                   # rev4 H2 — await BEFORE the isinstance check, otherwise
#                   # ``isinstance(coroutine, QuerySet)`` is False and the
#                   # visibility hook is silently skipped on async resolvers.
#                   async def _wrap(root: Any, info: Info):
#                       return await _post_process_async(
#                           target_type, await user_resolver(root, info), info
#                       )
#               else:
#                   def _wrap(root: Any, info: Info):
#                       return _post_process_sync(
#                           target_type, user_resolver(root, info), info
#                       )
#               # rev5 H1: NO runtime ``inspect.iscoroutine(result)`` fallback —
#               # ``functools.partial``-wrapped async resolvers are YAGNI;
#               # consumers rewrap in ``async def`` instead. Keeps the wrapper
#               # coverable under the 100% gate.
#               wrapped = _wrap
#
#           # ----- Slice 1 — Return the Strawberry field -----
#           # The factory returns the result of ``strawberry.field(...)``; the
#           # consumer's class-attribute annotation (``list[T]`` vs ``list[T] | None``)
#           # drives outer GraphQL-list nullability — Decision 1 + Decision 2,
#           # rev2 H2. ``description`` / ``deprecation_reason`` / ``directives``
#           # pass through unchanged so ``DjangoListField`` is feature-comparable
#           # with ``strawberry.field(...)`` at the metadata level.
#           return strawberry.field(
#               resolver=wrapped,
#               description=description,
#               deprecation_reason=deprecation_reason,
#               directives=directives,
#           )


# TODO(spec-016, Slice 1): Once the above is implemented, remove this module
# docstring's "SCAFFOLD" wording and add a real ``__all__ = ("DjangoListField",)``
# declaration. The re-export site is ``django_strawberry_framework/__init__.py``
# (Decision 1 — alphabetical position between ``BigInt`` and
# ``DjangoOptimizerExtension``); the ``__all__`` assertion in
# ``tests/base/test_init.py`` is updated in the SAME commit.
