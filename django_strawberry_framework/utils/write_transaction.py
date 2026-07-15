"""Write-transaction plumbing: the managed alias, alias pinning, row locks, and conflicts.

The BETA-055 hardening seam (mutation transactions): everything here exists so
the three write flavors (model / form / serializer) share ONE database
discipline instead of three drifting copies:

- **The managed write transaction.** ``DjangoSchema``'s execution context opens
  a ``transaction.atomic(using=alias)`` that spans GraphQL *response
  completion* (``schema.py::DjangoMutationExecutionContext``), so a payload
  that cannot be serialized rolls the write back instead of committing behind a
  ``data: null`` response. The pipeline refuses to write without it (this
  module's ``require_managed_write``): a generated mutation executed through a plain
  ``strawberry.Schema`` fails loudly BEFORE any database work, directing the
  consumer to ``DjangoSchema``.
- **One router write alias.** ``resolve_write_alias`` asks the router once per
  operation; every pipeline query - locate, visibility, relation checks, the
  post-write re-fetch, rollback marking - is pinned to that alias
  (``pin_write_queryset`` / the ``write_pipeline`` context the shared
  relation-check helpers consult). A custom ``get_queryset`` hook that
  re-routes to a DIFFERENT alias fails closed (``ConfigurationError``): the
  package offers single-transaction atomicity on one alias, never a pretend
  distributed transaction.
- **Row locks.** ``base_locked_queryset`` (the locate + relation-check paths) locks through the
  MODEL'S BASE MANAGER with the visibility queryset reduced to a pk subquery -
  never by attaching ``select_for_update()`` to an arbitrary consumer queryset,
  whose joins / unions / annotations a ``FOR UPDATE`` cannot legally carry.
  Backends without ``FOR UPDATE`` (sqlite) skip the clause silently, so the
  lock is a no-op there by Django's own contract.
- **Disappearing-row conflicts.** ``forced_update_conflict_errors`` maps a
  zero-row forced update to the in-band ``conflict`` ``FieldError`` - but ONLY
  when the transaction is still usable and the row is demonstrably absent;
  any other database error propagates and rolls back. Django 6.0 raises the
  typed ``Model.NotUpdated``; Django 5.2 raises a bare ``DatabaseError``, so
  the compat catch is version-sensitive (``not_updated_exceptions``).
"""

from __future__ import annotations

import threading
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from typing import Any

from django.db import DEFAULT_DB_ALIAS, DatabaseError, connections, router, transaction
from django.db.models.signals import pre_save

from ..exceptions import ConfigurationError
from ..utils.errors import field_error

# The alias of the completion-spanning transaction ``DjangoSchema``'s execution
# context opened for the mutation field currently executing. ``None`` means no
# managed transaction is open - i.e. the schema serving this operation is NOT a
# ``DjangoSchema`` - and the pipeline must refuse to write. A ``ContextVar`` so
# the flag follows the request across the ``sync_to_async`` boundary (asgiref
# copies the context into its worker thread) without threading a parameter
# through every resolver seam. This module lives in ``utils/`` (not
# ``mutations/``) so the shared queryset helpers can consult the write context
# without a utils -> mutations layering inversion.
_MANAGED_WRITE_ALIAS: ContextVar[str | None] = ContextVar(
    "django_strawberry_framework_managed_write_alias",
    default=None,
)

# The active write pipeline's (alias, lock) pair, set by the pipeline bodies for
# the duration of one operation so the SHARED relation-check helpers
# (``utils/querysets.py::stringified_pks_present`` and the form-path
# ``visible_related_object``/``s``) pin their queries to the write alias and
# apply the base-manager row lock - without forking their read-surface callers,
# which run with no context set and stay byte-identical in behavior.
_WRITE_PIPELINE: ContextVar[WriteAliasContext | None] = ContextVar(
    "django_strawberry_framework_write_pipeline",
    default=None,
)

# The plain-``strawberry.Schema`` refusal (fires BEFORE any database work).
_UNMANAGED_SCHEMA_MESSAGE = (
    "{name} must be executed through django_strawberry_framework.DjangoSchema. A plain "
    "strawberry.Schema commits the mutation's transaction when the resolver returns - BEFORE "
    "GraphQL response completion - so a completion failure would leave the write committed "
    "behind a null response. Build the schema as DjangoSchema(query=..., mutation=...)."
)


class WriteAliasContext:
    """The pinned ``(alias, lock)`` pair one write operation runs under.

    ``authorized_pk`` is the IMMUTABLE authorization snapshot the pipeline
    captures immediately after the update locate - BEFORE the permission hook
    or any other consumer-controlled code can touch the (mutable) located
    instance. ``None`` for create (no located row). The write flavors compare
    their saved result against THIS value, never against the live
    ``instance.pk`` a hook could have re-pointed.
    """

    __slots__ = ("alias", "authorized_pk", "lock")

    def __init__(self, alias: str, *, lock: bool) -> None:
        self.alias = alias
        self.lock = lock
        self.authorized_pk: Any = None


def resolve_write_alias(model: type | None) -> str:
    """Resolve the ONE router write alias the whole operation is pinned to.

    Asked once per operation (``router.db_for_write`` with no instance hint) and
    then pinned: the managed transaction, the locate, every relation check, the
    save / delete, the re-fetch, and the rollback all use this alias. A
    model-less plain form has no model to route, so it writes on
    ``DEFAULT_DB_ALIAS`` (Django's own no-hint fallback).
    """
    if model is None:
        return DEFAULT_DB_ALIAS
    return router.db_for_write(model)


@contextmanager
def managed_write_transaction(alias: str) -> Any:
    """Mark a completion-spanning transaction open on ``alias`` (the execution-context seam).

    Entered by ``DjangoMutationExecutionContext`` around each generated
    top-level mutation field (AFTER it opened ``transaction.atomic(using=alias)``)
    and consulted by ``require_managed_write``. Also the documented seam a
    direct-pipeline test wraps its call in (with its own ``transaction.atomic``)
    when it bypasses the schema.
    """
    token = _MANAGED_WRITE_ALIAS.set(alias)
    try:
        yield
    finally:
        _MANAGED_WRITE_ALIAS.reset(token)


def require_managed_write(mutation_cls: type) -> str:
    """Return the managed transaction's alias, or refuse the write (fail-before-write).

    The pipeline calls this FIRST - before the locate, before authorization,
    before any query - so a generated mutation reached through a plain
    ``strawberry.Schema`` (whose execution never opened the completion-spanning
    transaction) is a loud ``ConfigurationError`` naming the fix, never a write
    that could commit behind a failed response.
    """
    alias = _MANAGED_WRITE_ALIAS.get()
    if alias is None:
        raise ConfigurationError(_UNMANAGED_SCHEMA_MESSAGE.format(name=mutation_cls.__name__))
    return alias


@contextmanager
def write_pipeline(alias: str, *, lock: bool) -> Any:
    """Pin the shared relation-check helpers to ``alias`` (+ ``lock``) for one operation."""
    token = _WRITE_PIPELINE.set(WriteAliasContext(alias, lock=lock))
    try:
        yield
    finally:
        _WRITE_PIPELINE.reset(token)


@contextmanager
def pipeline_alias_guard(owner: str, alias: str) -> Any:
    """Reject EVERY SQL statement on a non-pinned connection for the guarded phase (fail closed).

    Installed by the pipeline skeletons around the consumer-reachable phases
    (permission hook, decode, validation, write, re-fetch), so consumer code
    anywhere in the pipeline - not just inside ``serializer.save()`` - cannot
    write through another database alias and escape the pinned transaction.

    The guard deliberately does NOT classify statements as reads vs writes: a
    lexical keyword test is not a reliable write boundary (leading SQL comments
    defeat a prefix match, PostgreSQL ``EXPLAIN ANALYZE UPDATE`` executes the
    write while starting with ``EXPLAIN``, and write-capable functions are
    invoked through ``SELECT``). The defensible single-alias contract is that
    the guarded phase talks to ONE database: every statement on a non-pinned
    connection raises ``ConfigurationError`` before it executes. Django
    connections are thread-local, so the ``execute_wrapper`` net polices only
    this request's thread; the ``pre_save`` receiver (a global signal) is
    thread-scoped explicitly, and exists only to give the ``Model.save()`` path
    a clearer, earlier error - before Django even opens the cross-alias
    connection.
    """
    guard_thread = threading.get_ident()

    def _reject_statements(other: str) -> Any:
        def _reject(
            execute: Any,
            sql: Any,
            params: Any,
            many: Any,
            context: Any,
        ) -> Any:
            del execute, sql, params, many, context
            raise ConfigurationError(
                f"{owner}: a SQL statement was issued on database alias {other!r} during the "
                f"mutation pipeline, but the mutation's transaction is pinned to {alias!r}. "
                "The pipeline does not classify statements as reads or writes (comments, "
                "EXPLAIN ANALYZE, and write-capable functions defeat lexical classification), "
                "so EVERY statement on a non-pinned alias is rejected during the guarded "
                "phase. Route all queries through the pinned write alias.",
            )

        return _reject

    def _block_cross_alias_save(sender: Any, using: Any, **kwargs: Any) -> None:
        del kwargs
        if threading.get_ident() != guard_thread:
            return
        if using != alias:
            raise ConfigurationError(
                f"{owner}: the mutation pipeline attempted to save a {sender.__name__} row on "
                f"database alias {using!r}, but the mutation's transaction is pinned to "
                f"{alias!r}; a write outside the pinned alias would escape the transaction "
                "(it could not be rolled back with the mutation). Route the custom save "
                "through the pinned write alias.",
            )

    with ExitStack() as stack:
        for other in connections:
            if other == alias:
                continue
            stack.enter_context(connections[other].execute_wrapper(_reject_statements(other)))
        pre_save.connect(_block_cross_alias_save, weak=False)
        try:
            yield
        finally:
            pre_save.disconnect(_block_cross_alias_save)


def current_write_pipeline() -> WriteAliasContext | None:
    """Return the active write pipeline's pinned context (``None`` on a read surface)."""
    return _WRITE_PIPELINE.get()


def require_write_pipeline() -> WriteAliasContext:
    """Return the active write pipeline context; absent one is an internal misuse.

    For pipeline internals (the forced-update save) that run strictly inside a
    ``write_pipeline(...)`` block: reaching this without one means a write step
    was invoked outside the pipeline skeleton, which is a wiring bug, not a
    runtime condition to tolerate.
    """
    context = _WRITE_PIPELINE.get()
    if context is None:
        raise ConfigurationError(
            "A mutation write step ran outside the write pipeline context; write steps are "
            "only callable from the pipeline skeleton (run_write_pipeline_sync / _run_delete).",
        )
    return context


def pin_write_queryset(queryset: Any, alias: str, *, owner: str | None = None) -> Any:
    """Pin ``queryset`` to the write alias; a hook that switched aliases fails closed.

    A visibility ``get_queryset`` hook may legitimately return the queryset
    un-routed (``_db`` unset - the normal case; the read-vs-write router split
    means its DEFAULT read alias differing from the write alias is NOT a hook
    decision, so ``queryset.db`` cannot be the test). But a hook that EXPLICITLY
    re-routed to a different alias (``.using("other")``) is asking for a
    cross-database write pipeline the package does not offer: honoring it would
    put the locate / relation checks outside the write transaction (reading
    uncommitted-invisible state) while pretending one atomic boundary covers
    both. Fail closed instead of writing.
    """
    hook_alias = queryset._db  # ``None`` unless the hook called ``.using(...)``.
    if hook_alias is not None and hook_alias != alias:
        if owner is None:
            owner = f"{queryset.model.__name__} get_queryset"
        raise ConfigurationError(
            f"{owner} returned a queryset routed to alias {hook_alias!r}, but this mutation's "
            f"write transaction is pinned to alias {alias!r}. A write pipeline runs every query "
            "inside ONE transaction on the write alias; cross-alias writes are not supported. "
            "Remove the .using(...) call or fix the database router.",
        )
    return queryset.using(alias)


def check_instance_write_alias(model: type, alias: str, instance: Any) -> None:
    """Re-check the router WITH the located instance before writing (fail closed on divergence).

    ``resolve_write_alias`` necessarily routed without an instance (the row was
    not yet located). An instance-sensitive router (sharding by row state) may
    answer differently once the instance is known - and by then the transaction,
    the lock, and the visibility reads are already pinned to the first answer.
    Writing to the second alias would silently escape the transaction, so a
    divergence is a loud ``ConfigurationError`` before any write.
    """
    instance_alias = router.db_for_write(model, instance=instance)
    if instance_alias is not None and instance_alias != alias:
        raise ConfigurationError(
            f"The database router routes {model.__name__} writes to {instance_alias!r} for this "
            f"instance, but the mutation's transaction is pinned to {alias!r} (the no-instance "
            "answer). An instance-sensitive write router cannot be honored mid-pipeline; make "
            "db_for_write deterministic for this model.",
        )


def base_locked_queryset(model: type, alias: str, visible_queryset: Any) -> Any:
    """Build the ``SELECT ... FOR UPDATE`` base query constrained by the visibility pk subquery.

    The lock rides the model's BASE MANAGER - a plain single-table query that can
    legally carry ``FOR UPDATE`` - with the (already alias-pinned) visibility
    queryset reduced to a ``pk__in`` subquery. Attaching ``select_for_update()``
    to the consumer's own queryset instead would break on the shapes a custom
    ``get_queryset`` may carry (outer joins, unions, annotations - Postgres
    rejects ``FOR UPDATE`` on several of them). Visibility is still enforced (a
    hidden row is not in the subquery, so it is not locked and not found).
    """
    return (
        model._base_manager.using(alias)
        .select_for_update()
        .filter(pk__in=visible_queryset.values("pk"))
    )


def conflict_error() -> Any:
    """Build the in-band concurrent-write ``conflict`` ``FieldError`` on ``id``.

    The disappearing-row envelope: the target existed at locate but a concurrent
    transaction removed (or made unwritable) it before this one finished. Keyed
    to ``id`` like the not-found envelope - the failure is about the addressed
    row - with the distinct ``conflict`` code so a client can retry rather than
    treat it as a permanent miss.
    """
    return field_error(
        "id",
        "The row was changed or removed by a concurrent operation; retry.",
        codes="conflict",
    )


def not_updated_exceptions(model: type) -> tuple[type[BaseException], ...]:
    """Return the exception types a zero-row forced update raises on this Django.

    Django 6.0 raises the typed per-model ``Model.NotUpdated`` (an
    ``ObjectNotUpdated`` + ``DatabaseError`` subclass); Django 5.2 has no typed
    exception and raises a bare ``DatabaseError`` ("Forced update did not affect
    any rows."). On the 5.2 fallback the broad catch is disambiguated by
    ``forced_update_conflict_errors``'s usable-transaction + row-absent probe,
    so a genuine backend error still propagates.
    """
    not_updated = getattr(model, "NotUpdated", None)
    if not_updated is not None:
        return (not_updated,)
    return (DatabaseError,)


def forced_update_conflict_errors(instance: Any, alias: str, exc: BaseException) -> list[Any]:
    """Map a zero-row forced update to the ``conflict`` envelope, or re-raise ``exc``.

    The compat disambiguation (Django 5.2's zero-row signal is an untyped
    ``DatabaseError``): the exception is a concurrent-delete conflict ONLY when

    1. the transaction on ``alias`` is still usable (Django raised the zero-row
       signal in Python; a real backend error would have poisoned the
       connection / marked it ``needs_rollback``), and
    2. the row is demonstrably absent (a base-manager ``exists()`` probe - the
       forced update matched zero rows because the row is gone, not because of
       some other update anomaly).

    Anything else re-raises: a genuine database error must propagate and roll
    the transaction back, never be swallowed into a retryable envelope.
    """
    connection = transaction.get_connection(using=alias)
    if not connection.needs_rollback:
        model = type(instance)
        try:
            row_present = model._base_manager.using(alias).filter(pk=instance.pk).exists()
        except DatabaseError:
            # The probe itself failed (a poisoned transaction the flag did not
            # reflect): the ORIGINAL error is the one that must propagate.
            raise exc from None
        if not row_present:
            return [conflict_error()]
    raise exc
