"""Write-transaction plumbing: the managed alias, alias pinning, row locks, and conflicts.

The 0.0.14 mutation write-hardening seam: everything here exists so
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
from django.db.models.fields.files import FieldFile
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

    ``target_state`` is the companion snapshot of the located instance's LOADED
    concrete field values, captured at the same immediately-after-locate moment;
    the serializer flavor rejects in-memory target drift against it before
    saving (a permission method / hook / validator that ``setattr``-ed the
    located row cannot smuggle unvalidated values into the write).

    ``write_phase`` is the pipeline-phase flag ``pipeline_alias_guard`` consults:
    ``False`` (the default) means the operation is in a database-READ-ONLY phase
    (permission checks, decoding, hooks, validation, save-kwargs preparation) and
    write SQL on the PINNED alias is rejected too; the flavor write steps flip it
    ``True`` via ``pipeline_write_phase()`` for exactly the duration of their
    actual save / delete call.

    ``auth_phase`` / ``auth_aliases`` scope the ONE narrow non-pinned exception
    the guard grants: while ``authorization_phase()`` is open (only around the
    single permission-evaluation call), statements are permitted on the explicitly
    identified ``auth_aliases`` - the aliases the auth machinery (the user model,
    ``auth.Permission`` / ``Group``, ``contenttypes``) reads from, which a
    divergent read/write router legitimately keeps off the write alias. Containment
    is transactional, not lexical: ``authorization_phase()`` runs each non-pinned
    auth alias inside a database-enforced read-only, rolled-back barrier transaction,
    so no ORDINARY write there commits outside the pinned transaction (the model
    trusts permission backends to read only - it is not a sandbox against deliberate
    volatile side effects; see ``authorization_phase``). The exception closes the
    instant authorization returns: decode / hooks / validation get the strict
    single-alias guard (a hook cannot reach the auth alias). This replaces the old
    pre-guard permission-cache warming.
    """

    __slots__ = (
        "alias",
        "auth_aliases",
        "auth_phase",
        "authorized_pk",
        "lock",
        "target_state",
        "write_phase",
    )

    def __init__(self, alias: str, *, lock: bool) -> None:
        self.alias = alias
        self.lock = lock
        self.authorized_pk: Any = None
        self.target_state: dict[str, Any] | None = None
        self.write_phase: bool = False
        self.auth_phase: bool = False
        self.auth_aliases: frozenset[str] = frozenset()


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
def pipeline_write_phase() -> Any:
    """Mark the pinned-alias WRITE phase open for the duration of one save / delete call.

    Entered by the flavor write steps around exactly the statement-issuing write
    (``Model.save()`` + the M2M assignment, ``form.save()``, ``serializer.save()``,
    ``instance.delete()``) and consulted by ``pipeline_alias_guard``'s pinned-alias
    wrapper: outside this block the whole pipeline is database-READ-ONLY, so a
    permission method, a hook, or a validator that issues write SQL - even on the
    CORRECT alias - fails loudly instead of committing a side effect the phase
    contract says cannot exist yet.
    """
    context = require_write_pipeline()
    previous = context.write_phase
    context.write_phase = True
    try:
        yield
    finally:
        context.write_phase = previous


# The backends whose non-pinned auth alias can be placed in a DATABASE-ENFORCED
# read-only transaction from an already-open ``atomic``. A vendor absent from this
# set cannot (e.g. MySQL only honours ``START TRANSACTION READ ONLY`` at BEGIN,
# which Django has already issued), so the auth phase FAILS CLOSED there rather
# than relying on forced rollback alone.
#
# NOTE the scope of "read-only" here. Backend read-only enforcement blocks ordinary
# DML/DDL (INSERT/UPDATE/DELETE/CREATE/...), which - together with the caller's
# forced rollback - is defense-in-depth against a permission backend accidentally
# WRITING on the auth alias. It is NOT a complete sandbox against a HOSTILE backend:
# PostgreSQL documents ``SET TRANSACTION READ ONLY`` as a high-level restriction that
# still permits side-effecting functions (``nextval``/``setval`` advance a sequence
# and are never rolled back; ``pg_advisory_lock`` at session scope outlives the
# transaction). The package's security model therefore TRUSTS permission backends to
# perform reads only; the barrier contains ordinary writes, not deliberate volatile
# side effects. Divergent-router authorization that cannot make that trust assumption
# must use genuinely capability-restricted database credentials instead.
_READ_ONLY_BARRIER_VENDORS = frozenset({"postgresql", "sqlite"})


def _enforce_read_only_barrier(barrier_alias: str) -> Any:
    """Put ``barrier_alias`` in a DB-enforced read-only transaction; fail closed if impossible.

    Forced rollback alone is not a portable barrier against ordinary writes: on
    backends with non-transactional tables or implicitly-committed DDL, a permission
    backend's ordinary write could still escape a rolled-back transaction. So the
    barrier is ALSO backed by the database's own read-only enforcement, where ordinary
    DML/DDL is rejected by the server; the caller's forced rollback stays as additional
    containment. A backend that cannot provide even that guarantee raises here (fail
    closed). This is defense-in-depth for ordinary writes, NOT a sandbox against a
    hostile backend deliberately invoking side-effecting functions (see the module
    note on sequences / session advisory locks): the model trusts permission backends
    to read only.

    Returns a zero-arg disarm callback. For a transaction-scoped mode (PostgreSQL) the
    disarm is a no-op; for a CONNECTION-level flag (SQLite ``PRAGMA query_only``) the
    disarm restores the flag's PRIOR value - never a blind OFF - so a pre-existing
    read-only setting or an ENCLOSING barrier's arming survives (nested barriers are
    stack-safe by save/restore). Runs inside the already-open barrier ``atomic`` while
    the auth phase is active, so the statements pass ``pipeline_alias_guard``.
    """
    connection = connections[barrier_alias]
    vendor = connection.vendor
    if vendor not in _READ_ONLY_BARRIER_VENDORS:
        raise ConfigurationError(
            f"The mutation authorization phase must resolve permissions on database alias "
            f"{barrier_alias!r} (a divergent auth/write router), but the {vendor!r} backend "
            "cannot be placed in a database-enforced read-only transaction from an already-open "
            "atomic block, so a permission backend's writes there could not be guaranteed "
            "contained. Route authentication and the write to the same alias, or use a backend "
            "that supports a read-only transaction (PostgreSQL / SQLite).",
        )
    if vendor == "postgresql":
        # Binds the CURRENT transaction; any ordinary DML/DDL raises at the server, and
        # the mode dies when the barrier atomic rolls back - nothing to restore.
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
        return lambda: None
    # SQLite ``PRAGMA query_only`` is a CONNECTION flag that OUTLIVES the transaction,
    # so read the prior value first and restore exactly that on disarm. A blind OFF
    # would clobber a pre-existing ON and, worse, break reentrancy: an inner auth phase
    # on the same connection would disarm the OUTER phase, leaving the outer guard
    # permitting auth-alias SQL on a now-writable connection.
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA query_only")
        row = cursor.fetchone()
        previously_on = bool(row[0]) if row else False
        cursor.execute("PRAGMA query_only = ON")
    restore = "ON" if previously_on else "OFF"

    def _disarm() -> None:
        with connection.cursor() as cursor:
            cursor.execute(f"PRAGMA query_only = {restore}")

    return _disarm


@contextmanager
def authorization_phase(auth_aliases: Any) -> Any:
    """Open the dedicated AUTHORIZATION phase: auth-alias access inside a rolled-back transaction.

    Wraps EXACTLY the single permission-evaluation call inside the alias guard.
    A divergent read/write router keeps the auth machinery (the request user, the
    permission set) off the write alias, so those queries would otherwise be
    rejected as cross-alias. For the phase duration this permits statements on the
    explicitly identified ``auth_aliases`` (see ``resolve_auth_aliases``) - but
    the CONTAINMENT is transactional, not lexical: every NON-pinned auth alias runs
    inside a ``transaction.atomic`` that is put in a DATABASE-ENFORCED read-only mode
    (``_enforce_read_only_barrier``) AND unconditionally rolled back when the phase
    ends. Forced rollback alone is not a portable barrier even against ordinary
    writes - on backends with non-transactional tables or implicitly-committed DDL an
    ordinary write could escape - so the barrier is ALSO backed by the database's own
    read-only enforcement (ordinary DML/DDL is rejected by the server), with the
    forced rollback kept as additional containment; a backend that cannot provide even
    that guarantee FAILS CLOSED. (Lexical read/write classification is deliberately NOT
    used here: a keyword test cannot safely authorize cross-alias execution.)

    This is NOT a complete sandbox against a hostile permission backend. Backend
    read-only mode is a high-level restriction: side-effecting functions still slip
    through (PostgreSQL ``nextval``/``setval`` advance a sequence and are never rolled
    back; a session-scope ``pg_advisory_lock`` outlives the transaction). The package's
    security model therefore TRUSTS permission backends to perform reads only; the
    barrier contains ordinary/accidental writes as defense-in-depth, not deliberate
    volatile side effects. A deployment that cannot make that trust assumption must
    give divergent-router authorization genuinely capability-restricted credentials.
    The pinned alias is already inside the mutation's own transaction and is never
    wrapped again; its phase-ordering guard is unchanged.

    The exception is scoped to this phase alone: once authorization returns the
    barrier transactions roll back and the phase closes, so decode / hooks /
    validation run under the strict single-alias guard again (they cannot touch
    the auth alias at all). An empty ``auth_aliases`` (a mutation with no
    permission classes) makes this a no-op - nothing is granted, nothing wrapped.
    """
    context = require_write_pipeline()
    aliases = frozenset(auth_aliases)
    # The pinned alias is already transactional (the mutation's own atomic); only
    # NON-pinned auth aliases need the rolled-back read-only barrier transaction.
    barrier_aliases = [alias for alias in aliases if alias != context.alias]
    prev_phase = context.auth_phase
    prev_aliases = context.auth_aliases
    context.auth_phase = True
    context.auth_aliases = aliases
    disarms: list[Any] = []
    try:
        try:
            with ExitStack() as stack:
                # Opened AFTER auth_phase is set so the barrier's own BEGIN + read-only
                # arming pass the guard. A rejected write poisons the atomic (Django
                # forbids further queries until it ends), so the connection-level
                # disarm (e.g. SQLite ``PRAGMA query_only = OFF``) must run only AFTER
                # the atomics have rolled back - hence the separate ``disarms`` list
                # unwound in the outer ``finally`` rather than a stack callback.
                for barrier_alias in barrier_aliases:
                    stack.enter_context(transaction.atomic(using=barrier_alias))
                    disarms.append(_enforce_read_only_barrier(barrier_alias))
                try:
                    yield
                finally:
                    for barrier_alias in barrier_aliases:
                        transaction.set_rollback(True, using=barrier_alias)
        finally:
            # The atomics have exited (rolled back) here, so the connections are in a
            # clean state and restoring a connection-level read-only flag cannot hit a
            # poisoned transaction. Still inside the auth phase, so the guard permits
            # the disarm statement on the auth alias.
            for disarm in disarms:
                disarm()
    finally:
        context.auth_phase = prev_phase
        context.auth_aliases = prev_aliases


# The read-only-phase allow-list: after stripping leading whitespace + SQL
# comments, a statement in the read-only phase may only begin with one of these
# tokens. ``SELECT`` is the pipeline's reads; the savepoint verbs are Django's
# own nested-``atomic`` bookkeeping (which rides the same ``execute_wrapper``
# chain on some backends). Everything else - INSERT / UPDATE / DELETE / DDL /
# ``EXPLAIN`` (PostgreSQL ``EXPLAIN ANALYZE`` EXECUTES the statement) / ``WITH``
# (a data-modifying CTE writes through a read-shaped opener) - is rejected.
_READ_ONLY_SQL_PREFIXES = (
    "SELECT",
    "SAVEPOINT",
    "RELEASE",
    "ROLLBACK",
)


def _sql_statement_token(sql: Any) -> str:
    """Return the first meaningful (comment-stripped, uppercased) token of ``sql``."""
    text = sql if isinstance(sql, str) else str(sql)
    index = 0
    length = len(text)
    while index < length:
        if text[index].isspace():
            index += 1
        elif text.startswith("--", index):
            newline = text.find("\n", index)
            if newline == -1:
                return ""
            index = newline + 1
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end == -1:
                return ""
            index = end + 2
        else:
            break
    rest = text[index:]
    return rest.split(None, 1)[0].upper() if rest else ""


def is_read_only_sql(sql: Any) -> bool:
    """Best-effort classify ``sql`` as read-only for the PINNED-alias phase guard.

    Comment-stripping + an ALLOW-list (never a write-keyword deny-list): a
    statement is read-only only when its first meaningful token is ``SELECT`` or
    a savepoint verb. This is deliberately conservative and still LEXICAL - a
    write-capable function invoked through ``SELECT`` passes - but on the pinned
    alias the classification is a PHASE-ORDERING check, not the atomicity or
    alias boundary: a statement that slips through still runs inside the pinned
    transaction and rolls back with it. Cross-alias enforcement (where a lexical
    test WOULD be a security boundary) never uses this: non-pinned connections
    reject every statement outright.
    """
    return _sql_statement_token(sql) in _READ_ONLY_SQL_PREFIXES


@contextmanager
def pipeline_alias_guard(owner: str, alias: str) -> Any:
    """Police the pipeline's SQL by alias AND phase (fail closed).

    Installed by the pipeline skeletons around the consumer-reachable phases
    (permission hook, decode, validation, write, re-fetch), so consumer code
    anywhere in the pipeline - not just inside ``serializer.save()`` - cannot
    write through another database alias and escape the pinned transaction:

    - **Non-pinned connections reject EVERY statement** - with ONE narrow,
      phase-scoped exception. The guard deliberately does NOT classify statements
      as reads vs writes across aliases: a lexical keyword test is not a reliable
      write boundary (leading SQL comments defeat a prefix match, PostgreSQL
      ``EXPLAIN ANALYZE UPDATE`` executes the write while starting with
      ``EXPLAIN``, and write-capable functions are invoked through ``SELECT``).
      The defensible single-alias contract is that the guarded phase talks to ONE
      database. The exception: DURING the authorization phase
      (``authorization_phase()``, wrapping only the permission-evaluation call),
      statements on the explicitly identified ``auth_aliases`` are permitted so a
      divergent read/write router can resolve the user + permission set off the
      write alias. Crucially this does NOT rely on lexical read/write
      classification (which cannot safely authorize cross-alias execution):
      ``authorization_phase()`` runs each non-pinned auth alias inside a
      database-enforced read-only transaction that is unconditionally ROLLED BACK
      when the phase ends, so an ordinary write a permission backend issues there -
      including a write-capable function through ``SELECT`` or a ``SELECT INTO`` - is
      rejected by the server and/or discarded on rollback and cannot commit outside
      the pinned transaction (the model trusts permission backends to read only; it
      does not sandbox deliberate volatile side effects like sequence advances).
      The exception closes when authorization returns, so decode / hooks / validation
      cannot reach the auth alias at all.
    - **The pinned connection is phased.** Outside the flavor write step
      (``pipeline_write_phase()``), the pipeline is database-read-only:
      permission checks, decoding, hooks, validation, and save-kwargs
      preparation may read but never write, so a statement that is not
      read-only by the conservative ``is_read_only_sql`` allow-list is rejected.
      On the pinned alias this lexical classification is phase-ordering
      DISCIPLINE, NOT a security boundary - and deliberately so. Everything on
      the pinned connection runs inside the mutation's OWN ``transaction.atomic``,
      so a write the lexical check misses (a write-capable function invoked
      through ``SELECT``, a ``SELECT INTO``) does not escape any transaction: it
      commits or rolls back ATOMICALLY with the mutation, exactly like the
      flavor's own writes. It cannot commit "on its own" and it cannot reach
      another database. The security boundary the guard enforces is CROSS-ALIAS
      isolation, and that is transactional, never lexical (non-pinned aliases
      reject outright; the auth alias runs in a rolled-back barrier). A
      database-enforced read-only mode on the pinned connection for only the
      read phase is not achievable without splitting the mutation across
      transactions and forfeiting that single-transaction atomicity, so lexical
      discipline backed by atomicity is the deliberate contract here.

    Django connections are thread-local, so the ``execute_wrapper`` net polices
    only this request's thread; the ``pre_save`` receiver (a global signal) is
    thread-scoped explicitly, and exists only to give the ``Model.save()`` path
    a clearer, earlier error - before Django even opens the cross-alias
    connection.
    """
    guard_thread = threading.get_ident()
    pipeline = _WRITE_PIPELINE.get()

    def _reject_writes_outside_write_phase(
        execute: Any,
        sql: Any,
        params: Any,
        many: Any,
        context: Any,
    ) -> Any:
        if (pipeline is None or not pipeline.write_phase) and not is_read_only_sql(sql):
            raise ConfigurationError(
                f"{owner}: write SQL was issued on the pinned database alias {alias!r} "
                "OUTSIDE the mutation's write phase. Permission checks, decoding, hooks, "
                "and validation are database-read-only; writes happen only inside the "
                "flavor's save step. Move the side effect out of the read-only phase (or "
                "schedule it with transaction.on_commit).",
            )
        return execute(sql, params, many, context)

    def _reject_statements(other: str) -> Any:
        def _reject(
            execute: Any,
            sql: Any,
            params: Any,
            many: Any,
            context: Any,
        ) -> Any:
            # The ONE narrow exception: during the authorization phase, statements
            # on an identified auth alias are permitted. The CONTAINMENT is NOT this
            # allow decision - it is the database-enforced read-only, rolled-back
            # barrier transaction ``authorization_phase()`` opened on this alias: an
            # ordinary write (or write-capable function through SELECT, or SELECT INTO)
            # is rejected by the server and/or discarded on rollback, so it cannot
            # commit outside the pinned transaction. Lexical read/write classification
            # is deliberately NOT used - a keyword test cannot safely authorize
            # cross-alias execution. This trusts permission backends to read only; it
            # does not sandbox deliberate volatile side effects (see authorization_phase).
            if pipeline is not None and pipeline.auth_phase and other in pipeline.auth_aliases:
                return execute(sql, params, many, context)
            del execute, sql, params, many, context
            raise ConfigurationError(
                f"{owner}: a SQL statement was issued on database alias {other!r} during the "
                f"mutation pipeline, but the mutation's transaction is pinned to {alias!r}. "
                "The pipeline does not classify statements as reads or writes (comments, "
                "EXPLAIN ANALYZE, and write-capable functions defeat lexical classification), "
                "so EVERY statement on a non-pinned alias is rejected during the guarded "
                "phase (except auth-alias queries inside the authorization phase, which run "
                "in a rolled-back barrier transaction). Route all queries through the pinned "
                "write alias.",
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
        for name in connections:
            if name == alias:
                # The pinned connection gets the PHASE wrapper (write SQL only
                # inside the flavor's write phase); every other connection
                # rejects outright. Addressed through the same iteration so a
                # never-configured alias is not eagerly instantiated here.
                stack.enter_context(
                    connections[name].execute_wrapper(_reject_writes_outside_write_phase),
                )
                continue
            stack.enter_context(connections[name].execute_wrapper(_reject_statements(name)))
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


def canonical_pk(model: type, value: Any) -> Any:
    """Coerce ``value`` through ``model``'s pk field to its canonical Python form.

    The pk-equality primitive the pipeline compares authorization snapshots with:
    ``str()`` comparison is NOT canonical for every pk type (a ``UUIDField`` pk
    may surface as a dashed, un-dashed, or ``UUID``-typed value that stringifies
    differently while addressing the SAME row), so equality goes through the
    model pk field's OWN ``to_python`` conversion. An uncoercible value (a forged
    pk of the wrong shape) raises the field's ``ValidationError`` - callers use
    ``pks_match``, which maps that to "not equal" (fail closed).
    """
    return model._meta.pk.to_python(value)


def pks_match(model: type, first: Any, second: Any) -> bool:
    """Compare two pk values canonically through ``model``'s pk field (fail closed).

    ``True`` only when BOTH values coerce through the pk field's ``to_python``
    and the canonical forms are equal; an uncoercible side (a spoofed pk of the
    wrong shape) is a mismatch, never an exception the caller must handle.
    """
    try:
        return canonical_pk(model, first) == canonical_pk(model, second)
    except Exception:
        return False


# The mutable-in-place field-value container types the target-state snapshot must
# FINGERPRINT rather than alias (JSONField -> dict / list, ArrayField -> list, and
# so on). A genuinely immutable scalar (str / int / Decimal / UUID / datetime) is
# kept by reference: it cannot be mutated in place, so aliasing is safe. A
# ``FieldFile`` is NOT immutable - a hook can re-point ``instance.<file>.name`` in
# place on the SAME descriptor object - so it is snapshotted by its database-relevant
# ``name`` string (see ``_FileNameSnapshot``), never aliased.
_MUTABLE_SNAPSHOT_TYPES = (
    dict,
    list,
    set,
    frozenset,
    tuple,
    bytearray,
)


class _FileNameSnapshot:
    """A ``FieldFile``'s database-relevant value (its ``name``), captured by value.

    ``FieldFile`` is a MUTABLE descriptor: a permission method / hook / validator can
    assign ``instance.<file>.name = ...`` in place, leaving the snapshot and the live
    attribute the same object so an identity/``==`` drift check short-circuits and DRF's
    whole-instance save persists the unauthorized file-column change. Snapshotting the
    immutable ``name`` string instead makes that drift detectable.
    """

    __slots__ = ("name",)

    def __init__(self, name: Any) -> None:
        self.name = name


# The node budget for one field value's structural fingerprint. Consumer-
# controlled JSON / array data is walked ITERATIVELY (no recursion, so a
# pathologically deep value cannot raise ``RecursionError`` mid-pipeline); a
# value with more nodes than this is rejected loudly rather than walked unbounded.
_SNAPSHOT_NODE_BUDGET = 100_000


class _SnapshotClose:
    """A structural close-marker on the fingerprint stack (distinct from any field value)."""

    __slots__ = ("token",)

    def __init__(self, token: str) -> None:
        self.token = token


class _FieldFingerprint:
    """A field value's iterative structural fingerprint (compared by digest, never deep-walked)."""

    __slots__ = ("digest",)

    def __init__(self, digest: str) -> None:
        self.digest = digest


def _field_fingerprint(value: Any) -> str:
    """Canonically serialize a mutable container value to a token string, ITERATIVELY.

    An explicit stack (never recursion) walks nested dict / list / tuple / set /
    bytes, so a JSONField / ArrayField value deeper than Python's recursion limit
    is fingerprinted without a ``RecursionError``; a node budget caps total work
    (a value exceeding it is a loud ``ConfigurationError``, not an unbounded walk).
    Dict keys and set members are emitted in a deterministic order so structurally
    equal values fingerprint identically. Scalars are tagged by type so ``1`` and
    ``"1"`` never collide.
    """
    parts: list[str] = []
    stack: list[Any] = [value]
    nodes = 0
    while stack:
        item = stack.pop()
        if type(item) is _SnapshotClose:
            parts.append(item.token)
            continue
        nodes += 1
        if nodes > _SNAPSHOT_NODE_BUDGET:
            raise ConfigurationError(
                "A located row's field value is too large to fingerprint for pre-save "
                "drift detection (exceeded the node budget). Reject rather than risk an "
                "unbounded walk of consumer-controlled data.",
            )
        if isinstance(item, dict):
            parts.append("{")
            stack.append(_SnapshotClose("}"))
            for key in sorted(item, key=repr, reverse=True):
                stack.append(item[key])
                stack.append(_SnapshotClose(f"={key!r}="))
        elif isinstance(item, (list, tuple)):
            parts.append("[")
            stack.append(_SnapshotClose("]"))
            stack.extend(reversed(item))
        elif isinstance(item, (set, frozenset)):
            parts.append("s{")
            stack.append(_SnapshotClose("}s"))
            stack.extend(sorted(item, key=repr, reverse=True))
        elif isinstance(item, (bytes, bytearray)):
            parts.append(f"b:{bytes(item)!r}")
        else:
            parts.append(f"{type(item).__name__}:{item!r}")
    return "".join(parts)


def _snapshot_field_value(value: Any) -> Any:
    """Snapshot a field value by value: fingerprint containers, name-capture files, alias scalars."""
    if isinstance(value, FieldFile):
        return _FileNameSnapshot(value.name)
    if isinstance(value, _MUTABLE_SNAPSHOT_TYPES):
        return _FieldFingerprint(_field_fingerprint(value))
    return value


def snapshot_target_state(instance: Any) -> dict[str, Any]:
    """Snapshot the located instance's LOADED concrete field values (pre-consumer-code).

    Captured by the pipeline skeleton at the same immediately-after-locate moment
    as ``authorized_pk`` - before the permission hook, the first
    consumer-controlled code, can touch the mutable instance. Only fields the
    locate actually LOADED are captured (a deferred field would lazy-load on
    ``getattr``, and its absence from the snapshot must not read as drift);
    the mutation locate never defers, so in practice this is every concrete
    non-M2M column. Mutable container values (a ``JSONField`` dict / list, an
    ``ArrayField`` list) are captured as an ITERATIVE structural FINGERPRINT
    (``_FieldFingerprint``) independent of the live instance: consumer code that
    mutates one IN PLACE (``instance.data["x"] = ...``) would otherwise drift
    undetected, since a by-reference snapshot would alias the same object the
    drift check reads back. The fingerprint (not a deep copy) also means the drift
    check is a flat digest compare, never a recursive structural walk that could
    ``RecursionError`` on deep data. Immutable scalars are kept by reference.
    """
    deferred = instance.get_deferred_fields()
    return {
        field.attname: _snapshot_field_value(getattr(instance, field.attname))
        for field in instance._meta.concrete_fields
        if field.attname not in deferred
    }


def assert_no_target_drift(owner: str, instance: Any) -> None:
    """Reject in-memory drift of the located target before the write (fail closed).

    Compares the instance's CURRENT loaded concrete field values against the
    pipeline's post-locate ``target_state`` snapshot. Consumer code between the
    locate and the save (a permission method, a serializer hook, a validator)
    must treat the located row as read-only: an attribute it re-pointed would
    otherwise ride into ``serializer.save()`` as an unvalidated write (DRF's
    ``update()`` saves the WHOLE instance, not just ``validated_data``). Called
    by the serializer flavor immediately before ``serializer.save()``; the model
    / form flavors legitimately mutate the instance inside their own write steps
    and do not use this check.
    """
    context = require_write_pipeline()
    snapshot = context.target_state
    if snapshot is None:
        return
    deferred = instance.get_deferred_fields()
    for attname, value in snapshot.items():
        if attname in deferred:
            continue
        current = getattr(instance, attname)
        if isinstance(value, _FileNameSnapshot):
            # A FieldFile: compare the database-relevant ``name`` (a hook that mutates
            # ``instance.<file>.name`` in place keeps the SAME descriptor object, so an
            # identity/``==`` check would miss it). A hook that replaced the attribute
            # with a non-FieldFile is drift too - compare the raw value then.
            current_name = current.name if isinstance(current, FieldFile) else current
            drifted = current_name != value.name
        elif isinstance(value, _FieldFingerprint):
            # A mutable container: compare the RECOMPUTED iterative fingerprint
            # (a flat digest ``!=``, never a recursive structural walk of what may
            # be deep consumer data).
            drifted = _field_fingerprint(current) != value.digest
        else:
            # An immutable scalar snapshotted by reference.
            drifted = current is not value and current != value
        if drifted:
            raise ConfigurationError(
                f"{owner}: the located, authorized row was mutated in memory before the "
                f"write ({type(instance).__name__}.{attname} changed between the locate "
                "and the save). Permission methods, hooks, and validators must not write "
                "to the target instance; changes go through the validated serializer data.",
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
