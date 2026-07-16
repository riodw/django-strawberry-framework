"""``DjangoSchema`` - the schema whose mutation transactions span response completion.

The BETA-055 commit-gap fix. A generated mutation's write pipeline runs inside
``transaction.atomic()``, but graphql-core *completes* (serializes) the returned
payload only after the resolver returns - historically after that transaction had
already committed. A completion failure (a non-nullable field resolving ``null``,
a corrupt scalar) therefore surfaced as ``data: null`` + a top-level error while
the write stayed committed: the client is told the mutation failed, the database
says it succeeded.

``DjangoMutationExecutionContext`` closes the gap at the only layer that sees
both sides: for each TOP-LEVEL generated mutation field it opens one
``transaction.atomic(using=<write alias>)`` BEFORE the resolver runs and exits it
only after graphql-core finished completing that field's value. Any error added
to the execution during that window - resolver-raised or completion-raised -
marks the transaction for rollback, so an unserializable payload rolls the write
back. The window also publishes the managed alias
(``utils/write_transaction.py::managed_write_transaction``), which the write pipeline
REQUIRES: a generated mutation executed through a plain ``strawberry.Schema``
fails before any database work, directing the consumer here.

Execution-mode split (spec plan "Implementation Changes"):

- **Sync** (``schema.execute_sync`` / the WSGI view): graphql-core completes the
  field synchronously inside ``execute_field``, so the context holds the
  transaction directly around the ``super()`` call on the calling thread.
- **Async** (``await schema.execute`` / ASGI / Channels): the ORM pipeline runs
  in ``sync_to_async(thread_sensitive=True)`` workers, and asgiref routes every
  ``thread_sensitive`` call from one async context onto the SAME thread - so the
  context opens the transaction in one such worker, awaits the field's
  completion, and closes it in another; open, pipeline, and close all share one
  thread and therefore one Django connection.

Mutation root fields execute serially (the GraphQL spec's mutation semantics,
graphql-core's ``execute_fields_serially``), so consecutive top-level mutation
fields get INDEPENDENT transactions: field two's transaction opens only after
field one's committed or rolled back.

Only fields whose resolver carries the ``DjangoMutationField`` marker are
wrapped; every other field (queries, consumer-written mutations, introspection)
executes exactly as stock graphql-core.
"""

from __future__ import annotations

from typing import Any

import strawberry
from django.db import transaction
from graphql.execution.execute import ExecutionContext
from strawberry.utils.inspect import in_async_context

from .mutations.fields import MUTATION_CLASS_MARKER
from .utils.querysets import run_in_one_sync_boundary
from .utils.write_transaction import managed_write_transaction, resolve_write_alias


class DjangoMutationExecutionContext(ExecutionContext):
    """Hold each generated mutation field's transaction open through value completion."""

    def execute_field(
        self,
        parent_type: Any,
        source: Any,
        field_nodes: Any,
        path: Any,
    ) -> Any:
        """Wrap a marked top-level mutation field in its completion-spanning transaction."""
        mutation_cls = self._marked_mutation_class(parent_type, field_nodes)
        if mutation_cls is None:
            return super().execute_field(parent_type, source, field_nodes, path)

        alias = resolve_write_alias(mutation_cls._mutation_meta.model)
        if in_async_context():
            return self._execute_mutation_field_async(
                alias,
                parent_type,
                source,
                field_nodes,
                path,
            )
        return self._execute_mutation_field_sync(alias, parent_type, source, field_nodes, path)

    def _marked_mutation_class(self, parent_type: Any, field_nodes: Any) -> type | None:
        """Return the field's bound mutation class, or ``None`` for any unmarked field.

        Only TOP-LEVEL mutation fields qualify (``parent_type`` is the schema's
        mutation root; ``execute_field`` also fires for every nested payload
        field, whose completion the already-open transaction covers). The marker
        is read through Strawberry's field extension
        (``extensions["strawberry-definition"].base_resolver.wrapped_func``) -
        the synthesized ``_resolve`` the ``DjangoMutationField`` factory stamped
        with its mutation class.
        """
        if parent_type is not self.schema.mutation_type:
            return None
        field_def = parent_type.fields.get(field_nodes[0].name.value)
        if field_def is None:  # introspection (``__typename``) has no field entry here.
            return None
        strawberry_field = (field_def.extensions or {}).get("strawberry-definition")
        base_resolver = getattr(strawberry_field, "base_resolver", None)
        wrapped = getattr(base_resolver, "wrapped_func", None)
        return getattr(wrapped, MUTATION_CLASS_MARKER, None)

    def _execute_mutation_field_sync(
        self,
        alias: str,
        parent_type: Any,
        source: Any,
        field_nodes: Any,
        path: Any,
    ) -> Any:
        """Sync execution: hold the transaction directly around resolve + completion.

        Under sync execution graphql-core completes the field's value INSIDE the
        ``super().execute_field`` call, so entering ``transaction.atomic`` before
        it and exiting after covers the whole resolve -> complete window on the
        calling thread. Any error appended to ``self.errors`` during the window
        (a resolver error is a *located* error, not an exception, so an
        exception-based rollback would miss it) marks the transaction for
        rollback before the block exits.
        """
        errors_before = len(self.errors)
        atomic = transaction.atomic(using=alias)
        atomic.__enter__()
        try:
            with managed_write_transaction(alias):
                result = super().execute_field(parent_type, source, field_nodes, path)
        except BaseException as exc:
            if not atomic.__exit__(type(exc), exc, exc.__traceback__):
                raise
            return None  # pragma: no cover - ``atomic.__exit__`` never suppresses.
        if len(self.errors) > errors_before:
            transaction.set_rollback(True, using=alias)
        atomic.__exit__(None, None, None)
        return result

    async def _execute_mutation_field_async(
        self,
        alias: str,
        parent_type: Any,
        source: Any,
        field_nodes: Any,
        path: Any,
    ) -> Any:
        """Async execution: open / close the transaction in the ``thread_sensitive`` worker.

        The ORM pipeline runs in ``sync_to_async(thread_sensitive=True)`` (the
        spec-036 AR-M4 one-worker boundary), and asgiref serializes every
        ``thread_sensitive`` call from this async context onto the SAME thread -
        so ``__enter__`` here, the pipeline's queries, and ``__exit__`` below all
        share one thread and one Django connection. The completion ``await``
        happens between them on the event loop; the transaction stays open on the
        worker's (idle) connection meanwhile, exactly the verified-prototype
        shape.
        """
        errors_before = len(self.errors)
        atomic = transaction.atomic(using=alias)
        await run_in_one_sync_boundary(atomic.__enter__)
        try:
            with managed_write_transaction(alias):
                result = super().execute_field(parent_type, source, field_nodes, path)
                if self.is_awaitable(result):
                    result = await result
        except BaseException as exc:
            # Bind the exception explicitly: the ``except`` name is cleared when
            # the block exits, so the worker-thread closure must not capture it.
            captured = exc

            def _exit_with_error() -> bool:
                return bool(atomic.__exit__(type(captured), captured, captured.__traceback__))

            if not await run_in_one_sync_boundary(_exit_with_error):
                raise
            return None  # pragma: no cover - ``atomic.__exit__`` never suppresses.

        def _exit_clean() -> None:
            if len(self.errors) > errors_before:
                transaction.set_rollback(True, using=alias)
            atomic.__exit__(None, None, None)

        await run_in_one_sync_boundary(_exit_clean)
        return result


class DjangoSchema(strawberry.Schema):
    """``strawberry.Schema`` with the mutation-transaction execution context installed.

    The REQUIRED schema class for any schema exposing generated mutations
    (``DjangoMutationField`` targets): the write pipeline refuses to run outside
    the managed transaction this schema's execution context opens. Drop-in
    otherwise - every constructor argument passes through, and a consumer
    needing a custom execution context subclasses
    ``DjangoMutationExecutionContext`` and passes it explicitly.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("execution_context_class", DjangoMutationExecutionContext)
        super().__init__(*args, **kwargs)
