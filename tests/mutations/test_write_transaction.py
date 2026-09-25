"""The mutation write-transaction contract (``DjangoSchema`` + ``utils/write_transaction.py``).

Completion-spanning transaction internals: the plain-``strawberry.Schema``
refusal, concurrent async windows on their own connections, ``BaseException``
unwind, the async window's private thread (another socket's connection hygiene,
client cancellation, an outer ``ThreadSensitiveContext``), the closed-connection
failure rule in both modes, disappearing-row ``conflict``, and fingerprint
helpers. Live HTTP (sync ``/graphql/`` and async ``/graphql-async/``) is
``examples/fakeshop/test_query/test_mutation_atomicity.py``. The socket rows sit
here rather than live because fakeshop has no WebSocket mount, and a WSGI
request cannot hold two windows open at once or cancel one mid-flight.
"""

from __future__ import annotations

import asyncio
import contextlib
import itertools
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
import strawberry
from apps.products import models as product_models
from asgiref.sync import ThreadSensitiveContext, async_to_sync, sync_to_async
from asgiref.testing import ApplicationCommunicator as AsgirefApplicationCommunicator
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.db import (
    DatabaseError,
    IntegrityError,
    close_old_connections,
    connections,
    transaction,
)
from django.db.backends.signals import connection_created
from django.db.backends.sqlite3 import base as sqlite_base
from django.db.models.signals import post_save
from strawberry import relay

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils import write_transaction
from django_strawberry_framework.utils.write_transaction import (
    _enforce_read_only_barrier,
    check_instance_write_alias,
    conflict_error,
    forced_update_conflict_errors,
    not_updated_exceptions,
    pin_write_queryset,
    pipeline_scoped_queryset,
    pipeline_write_phase,
    require_write_pipeline,
    resolve_write_alias,
    write_pipeline,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


_category_name_counter = itertools.count(1)


def _category_name() -> str:
    return f"WTCat-{next(_category_name_counter)}"


class _AllowAll:
    """Authorize every write (these tests pin the transaction, not the auth seam)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return True


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _declare_item_types(*, item_get_queryset=None):
    """Declare the Item/Category primaries (optionally with an Item visibility hook)."""

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            # ``created_date`` is the completion-failure lever: a raw-SQL
            # corrupted date hydrates to None and fails the non-nullable field
            # at completion (the async rollback tests select it).
            fields = ("id", "name", "created_date")
            primary = True

    item_body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": product_models.Item, "fields": ("id", "name", "category"), "primary": True},
        ),
    }
    if item_get_queryset is not None:
        item_body["get_queryset"] = item_get_queryset
    ItemT = type("ItemT", (DjangoType, relay.Node), item_body)
    return CategoryT, ItemT


def _declare_update_mutation(*, permission_classes=None, select_for_update=True):
    meta_attrs = {
        "model": product_models.Item,
        "operation": "update",
        "permission_classes": permission_classes
        if permission_classes is not None
        else [_AllowAll],
        "select_for_update": select_for_update,
    }
    return type("UpdateItem", (DjangoMutation,), {"Meta": type("Meta", (), meta_attrs)})


def _declare_delete_mutation(*, permission_classes=None, select_for_update=True):
    meta_attrs = {
        "model": product_models.Item,
        "operation": "delete",
        "permission_classes": permission_classes
        if permission_classes is not None
        else [_AllowAll],
        "select_for_update": select_for_update,
    }
    return type("DeleteItem", (DjangoMutation,), {"Meta": type("Meta", (), meta_attrs)})


def _mutation_schema(*mutations, schema_cls=DjangoSchema, extra_fields=None):
    """Build a probe schema over ``mutations``, with response-boundary masking OFF.

    The subject of this file is the WRITE pipeline - which alias a write is pinned
    to, whether a phase violation or a non-bool permission result fails closed, and
    whether the row survived. Several rows prove that by reading the
    ``ConfigurationError`` text the pipeline raised, and the spec-048 error policy
    would replace exactly that text with its stable message. The policy is therefore
    opted out of on these in-process probe schemas (``error_policy={"enabled":
    False}``) rather than claiming a debug deployment; masking is pinned on its own
    in ``tests/test_error_policy.py`` and the live tier. A plain
    ``strawberry.Schema`` takes no such argument and installs no extension, so the
    opt-out is passed only for the package schema class.
    """
    policy_kwargs = (
        {"error_policy": {"enabled": False}}
        if isinstance(schema_cls, type) and issubclass(schema_cls, DjangoSchema)
        else {}
    )
    body = {
        f"write{index}": DjangoMutationField(mutation_cls)
        for index, mutation_cls in enumerate(mutations)
    }
    if extra_fields:
        body.update(extra_fields)
    body["__annotations__"] = {}
    Mutation = strawberry.type(type("Mutation", (), body))
    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return schema_cls(
        query=_Query,
        mutation=Mutation,
        extensions=[lambda: optimizer],
        **policy_kwargs,
    )


def _item_gid(pk) -> str:
    return str(relay.GlobalID(type_name="products.item", node_id=str(pk)))


_UPDATE = (
    "mutation($id: ID!, $d: ItemPartialInput!){ write0(id:$id, data:$d){ "
    "node{ name } errors{ field messages } } }"
)
_DELETE = "mutation($id: ID!){ write0(id:$id){ node{ name } errors{ field messages } } }"


def _seed_item(name: str = "Seeded"):
    category = product_models.Category.objects.create(name=_category_name())
    return product_models.Item.objects.create(name=name, category=category)


# ===========================================================================
# The plain-Schema refusal (fail before any database work)
# ===========================================================================


@pytest.mark.django_db
def test_plain_strawberry_schema_refuses_generated_mutations_before_writing():
    """A generated mutation on a plain ``strawberry.Schema`` fails loudly, writing nothing."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem, schema_cls=strawberry.Schema)
    item = _seed_item("Untouched")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "Written"}},
    )

    assert result.errors is not None
    assert "DjangoSchema" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "Untouched"


# ===========================================================================
# Async execution internals (concurrent windows, BaseException)
# ===========================================================================


def _window_observation() -> tuple[int, bool, int]:
    """(thread, in an atomic block?, savepoint depth) of the calling thread's connection."""
    connection = connections["default"]
    return threading.get_ident(), connection.in_atomic_block, len(connection.savepoint_ids)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_concurrent_async_windows_each_hold_an_outermost_transaction_of_their_own(
    monkeypatch,
):
    """Two windows open at once on one loop never share a connection or a savepoint.

    Each window runs its thread-sensitive work on a thread of its own, so the
    second opens while the first is still open, and both observe an OUTERMOST
    atomic block (no savepoint) on two different threads.
    """
    from asgiref.sync import sync_to_async
    from graphql.execution.execute import ExecutionContext as CoreExecutionContext

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    both_open = asyncio.Event()
    observations: list[tuple[int, bool, int]] = []

    async def fake_execute_field(
        self,
        parent_type,
        source,
        field_nodes,
        path,
    ):
        observations.append(await sync_to_async(_window_observation, thread_sensitive=True)())
        if len(observations) == 2:
            both_open.set()
        await asyncio.wait_for(both_open.wait(), timeout=2)
        return None

    monkeypatch.setattr(CoreExecutionContext, "execute_field", fake_execute_field)
    variables = {"id": _item_gid(1), "d": {"name": "Concurrent"}}
    await asyncio.gather(
        schema.execute(_UPDATE, variable_values=variables),
        schema.execute(_UPDATE, variable_values=variables),
    )

    assert [(in_atomic, depth) for _, in_atomic, depth in observations] == [(True, 0), (True, 0)]
    assert observations[0][0] != observations[1][0]


@pytest.mark.django_db(transaction=True)
def test_concurrent_async_windows_on_two_event_loops_each_hold_their_own_transaction(
    monkeypatch,
):
    """Windows on separate event loops open side by side, each outermost on its own thread."""
    from concurrent.futures import ThreadPoolExecutor

    from asgiref.sync import sync_to_async
    from graphql.execution.execute import ExecutionContext as CoreExecutionContext

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    both_open = threading.Barrier(2, timeout=2)
    observations: list[tuple[int, bool, int]] = []
    observation_lock = threading.Lock()

    async def fake_execute_field(
        self,
        parent_type,
        source,
        field_nodes,
        path,
    ):
        observation = await sync_to_async(_window_observation, thread_sensitive=True)()
        with observation_lock:
            observations.append(observation)
        await asyncio.to_thread(both_open.wait)
        return None

    monkeypatch.setattr(CoreExecutionContext, "execute_field", fake_execute_field)
    variables = {"id": _item_gid(1), "d": {"name": "CrossLoop"}}

    def execute() -> None:
        asyncio.run(schema.execute(_UPDATE, variable_values=variables))

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(execute)
        second = executor.submit(execute)
        first.result()
        second.result()

    assert [(in_atomic, depth) for _, in_atomic, depth in observations] == [(True, 0), (True, 0)]
    assert observations[0][0] != observations[1][0]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_execution_context_exits_transaction_on_raised_base_exception(monkeypatch):
    """A non-GraphQL exception escaping the field still exits the worker transaction."""
    from asgiref.sync import sync_to_async
    from graphql.execution.execute import ExecutionContext as CoreExecutionContext

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = await sync_to_async(_seed_item)("AsyncRaise")

    def _boom(
        self,
        parent_type,
        source,
        field_nodes,
        path,
    ):
        raise RuntimeError("execution exploded outside GraphQL error handling")

    monkeypatch.setattr(CoreExecutionContext, "execute_field", _boom)
    # Strawberry's async execution surfaces the unexpected exception as a
    # result-level error; the load-bearing assertion is that the worker
    # transaction was exited (its connection left the atomic block).
    result = await schema.execute(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "AsyncRaised"}},
    )
    assert result.errors is not None
    assert "execution exploded" in str(result.errors[0])
    in_atomic = await sync_to_async(lambda: connections["default"].in_atomic_block)()
    assert in_atomic is False


@pytest.mark.django_db(transaction=True)
def test_sync_execution_context_exits_transaction_on_raised_base_exception(monkeypatch):
    """The sync twin: a non-GraphQL exception escaping the field exits the transaction."""
    from graphql.execution.execute import ExecutionContext as CoreExecutionContext

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("SyncRaise")

    def _boom(
        self,
        parent_type,
        source,
        field_nodes,
        path,
    ):
        raise RuntimeError("execution exploded outside GraphQL error handling")

    monkeypatch.setattr(CoreExecutionContext, "execute_field", _boom)
    # Strawberry's sync execution surfaces the unexpected exception as a
    # result-level error rather than re-raising; the load-bearing assertion is
    # that the transaction was exited (the connection left the atomic block).
    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "SyncRaised"}},
    )
    assert result.errors is not None
    assert "execution exploded" in str(result.errors[0])
    assert connections["default"].in_atomic_block is False


# ===========================================================================
# The async window owns its thread and connection
# ===========================================================================

#: Every row below names its categories under this prefix, and the committed-state
#: reader counts only these, so a row's assertion is about its own writes.
_WINDOW_PREFIX = "window-"

#: The field error of a window whose connection was closed inside its transaction.
#: RE-TYPED rather than imported, so a drift in the package text fails a row.
_CLOSED_WINDOW_MESSAGE = (
    "The database connection was closed before the mutation's transaction could "
    "commit; nothing was written."
)

_CREATE_CATEGORY = (
    "mutation($d: CategoryInput!){ write0(data:$d){ node{ id name } errors{ field messages } } }"
)
_CREATE_CATEGORY_TOUCHING = (
    "mutation($d: CategoryInput!){ write0(data:$d){ node{ id name touched } "
    "errors{ field messages } } }"
)


async def _touch_through_channels_database_sync_to_async(root) -> bool:
    """A consumer's async node field doing its ORM work the way Channels documents.

    ``channels.db.database_sync_to_async`` is thread-sensitive and runs Django's
    ``close_old_connections`` before and after its body, on whichever thread it
    lands - inside a window, the window's own.
    """
    del root
    return await database_sync_to_async(lambda: True)()


def _close_old_connections_in_a_resolver(root) -> bool:
    """A consumer's sync node field that runs Django's connection hygiene mid-request."""
    del root
    close_old_connections()
    return True


def _category_create_schema(*, touched=None):
    """A ``DjangoSchema`` exposing one generated Category create as ``write0``.

    ``touched`` becomes a consumer-authored ``touched`` field on the payload's node
    type, resolved during completion - inside the window.
    """
    body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
        ),
    }
    if touched is not None:
        body["touched"] = strawberry.field(resolver=touched)
    type("CategoryT", (DjangoType, relay.Node), body)
    meta_attrs = {
        "model": product_models.Category,
        "operation": "create",
        "permission_classes": [_AllowAll],
    }
    CreateCategory = type(
        "CreateCategory",
        (DjangoMutation,),
        {"Meta": type("Meta", (), meta_attrs)},
    )
    return _mutation_schema(CreateCategory)


def _create_variables(name: str) -> dict:
    return {"d": {"name": name}}


@contextlib.contextmanager
def _held_in_the_pipeline(name: str):
    """Park the window whose create writes ``name`` inside its pipeline until released.

    A ``post_save`` receiver - consumer application code, running on the window's
    thread right after the INSERT - blocks there, so the window's transaction is
    open and holds a write while the test acts. Yields ``(reached, release)``: an
    ``asyncio.Event`` set once the pipeline is parked and a ``threading.Event`` the
    test sets to let it continue.
    """
    loop = asyncio.get_running_loop()
    reached = asyncio.Event()
    release = threading.Event()

    def _park(sender, instance, **kwargs):
        del sender, kwargs
        if instance.name == name:
            loop.call_soon_threadsafe(reached.set)
            release.wait(10)

    post_save.connect(_park, sender=product_models.Category, weak=False)
    try:
        yield reached, release
    finally:
        release.set()
        post_save.disconnect(_park, sender=product_models.Category)


def _committed_window_names() -> set[str]:
    """The committed ``window-*`` category names, read on a connection no window uses.

    Meant to run on a thread of its own: the read sees only COMMITTED rows, and a
    write still held open by a stranded transaction makes it fail rather than pass.
    The thread's connection is closed before returning (its raw handle too, which
    an in-memory SQLite connection keeps through ``close()``), so nothing is left
    to the finalizer.
    """
    try:
        return set(
            product_models.Category.objects.filter(name__startswith=_WINDOW_PREFIX).values_list(
                "name",
                flat=True,
            ),
        )
    finally:
        connection = connections["default"]
        connection.close()
        if connection.connection is not None:
            connection.connection.close()
            connection.connection = None


async def _committed() -> set[str]:
    return await asyncio.to_thread(_committed_window_names)


@contextlib.contextmanager
def _connections_really_close():
    """Make a ``close()`` of the test database's connections actually close them.

    A no-op on the Postgres tier, where a close is always real. The default tier's
    in-memory SQLite backend declines every close request (closing would destroy
    the database), so a connection closed inside a window could never be observed
    there. For the duration this lifts that refusal, with a keeper handle holding
    the shared-cache database alive, so a close does what it does on a file-backed
    or server database: the handle closes, SQLite rolls its open transaction back,
    and Django marks the connection ``closed_in_transaction``.
    """
    default = connections["default"]
    if default.vendor != "sqlite" or not default.is_in_memory_db():
        yield
        return
    keeper = sqlite3.connect(default.settings_dict["NAME"], uri=True)
    try:
        with patch.object(sqlite_base.DatabaseWrapper, "is_in_memory_db", lambda self: False):
            yield
    finally:
        # The database lives only while some handle holds it. A sync row closes the
        # calling thread's own connection, so that connection is reopened before
        # the keeper goes; an async row never closes the loop thread's connection.
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            default.ensure_connection()
        keeper.close()


class _HygieneWebsocketCommunicator(WebsocketCommunicator):
    """A WebSocket communicator that leaves Channels' connection hygiene switched on.

    ``channels.testing``'s communicator replaces ``channels.db.close_old_connections``
    with a no-op, process-wide, while it sends or receives. A real server runs the
    real one before every message it dispatches, and that call is the exposure the
    socket rows measure, so these two methods go straight to asgiref's base.
    """

    async def send_input(self, message):
        return await AsgirefApplicationCommunicator.send_input(self, message)

    async def receive_output(self, timeout=1):
        return await AsgirefApplicationCommunicator.receive_output(self, timeout)


async def _no_http_application(scope, receive, send):
    """The router's required HTTP application; the socket rows never reach it."""
    raise AssertionError("the window rows serve no HTTP")


def _window_router(schema):
    from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

    return DjangoGraphQLProtocolRouter(schema, django_application=_no_http_application)


@contextlib.asynccontextmanager
async def _socket(router):
    """One acknowledged ``graphql-transport-ws`` socket on ``router``."""
    communicator = _HygieneWebsocketCommunicator(
        router,
        "/graphql",
        headers=[(b"host", b"testserver"), (b"origin", b"http://testserver")],
        subprotocols=["graphql-transport-ws"],
    )
    connected, _subprotocol = await communicator.connect(timeout=10)
    assert connected, "websocket handshake failed"
    try:
        await communicator.send_json_to({"type": "connection_init"})
        ack = await communicator.receive_json_from(timeout=10)
        assert ack["type"] == "connection_ack", ack
        yield communicator
    finally:
        await communicator.disconnect()


async def _send_create(communicator, name: str, *, op_id: str = "1") -> None:
    await communicator.send_json_to(
        {
            "id": op_id,
            "type": "subscribe",
            "payload": {"query": _CREATE_CATEGORY, "variables": _create_variables(name)},
        },
    )


async def _receive_result(communicator, *, op_id: str = "1") -> dict:
    """The operation's single result frame, with its ``complete`` drained."""
    frame = await communicator.receive_json_from(timeout=10)
    if frame["type"] == "next":
        assert await communicator.receive_json_from(timeout=10) == {
            "type": "complete",
            "id": op_id,
        }
    return frame


def _reported_name(frame: dict) -> str | None:
    """The node name a success frame reports, or ``None`` for anything else."""
    payload = frame.get("payload") or {}
    if frame.get("type") != "next" or payload.get("errors"):
        return None
    node = ((payload.get("data") or {}).get("write0") or {}).get("node") or {}
    return node.get("name")


@pytest.mark.django_db(transaction=True)
async def test_another_sockets_message_mid_window_leaves_the_windows_write_committed():
    """A message dispatched on an unrelated socket cannot close an open window's connection.

    Channels runs ``close_old_connections`` before dispatching every message, on
    the thread-sensitive worker the dispatching socket reaches, and Django closes
    a connection it finds inside a transaction. The window's connection belongs
    to the window's own thread, so an unauthenticated socket's ``ping`` arriving
    while the window holds its write cannot reach it: the success payload the
    window reports is a committed row.
    """
    router = _window_router(_category_create_schema())
    name = "window-pinged"
    with _connections_really_close(), _held_in_the_pipeline(name) as (reached, release):
        async with _socket(router) as writer, _socket(router) as pinger:
            await _send_create(writer, name)
            await asyncio.wait_for(reached.wait(), timeout=10)
            await pinger.send_json_to({"type": "ping"})
            await asyncio.sleep(0.1)  # the ping's dispatch has queued its connection hygiene
            release.set()
            frame = await _receive_result(writer)
            assert (await pinger.receive_json_from(timeout=10))["type"] == "pong"

    assert _reported_name(frame) == name, frame
    assert name in await _committed()


@pytest.mark.django_db(transaction=True)
async def test_a_client_complete_mid_window_never_strands_its_transaction():
    """A client ``complete`` while the window is open cannot strand its transaction.

    Channels dispatches the ``complete`` frame only after the connection hygiene
    it queues on asgiref's shared thread-sensitive worker, and another context's
    sync call queues there too, so the cancellation lands while the window is
    finishing and its exit would wait behind that call. Cancelling an operation
    drops executor work that has not started, and the window's exit must never be
    such work: a fresh operation on another socket afterwards reports success AND
    is committed, which a transaction left open under it would prevent.
    """
    router = _window_router(_category_create_schema())
    loop = asyncio.get_running_loop()
    occupied = asyncio.Event()
    vacate = threading.Event()

    def _occupy_the_shared_worker() -> None:
        loop.call_soon_threadsafe(occupied.set)
        vacate.wait(10)

    name = "window-completed"
    with _held_in_the_pipeline(name) as (reached, release):
        async with _socket(router) as completing, _socket(router) as following:
            await _send_create(completing, name)
            await asyncio.wait_for(reached.wait(), timeout=10)
            await completing.send_json_to({"id": "1", "type": "complete"})
            await asyncio.sleep(0.05)  # the complete's dispatch has queued its hygiene
            occupant = asyncio.create_task(
                sync_to_async(_occupy_the_shared_worker, thread_sensitive=True)(),
            )
            await asyncio.sleep(0.05)
            release.set()
            await asyncio.wait_for(occupied.wait(), timeout=10)
            await asyncio.sleep(0.1)  # the cancellation has landed
            vacate.set()
            await occupant
            await _send_create(following, "window-following", op_id="2")
            frame = await _receive_result(following, op_id="2")

    assert _reported_name(frame) == "window-following", frame
    assert "window-following" in await _committed()


@pytest.mark.django_db(transaction=True)
async def test_a_window_cancelled_twice_while_held_rolls_back_and_the_next_mutation_commits():
    """Repeated cancellation of an open window still exits its transaction, rolled back.

    The second cancellation lands while the window's exit is queued behind the
    pipeline it interrupted. The exit still runs once the pipeline finishes, so
    the held write is rolled back rather than left open, and the next mutation
    commits on its own.
    """
    schema = _category_create_schema()
    with _held_in_the_pipeline("window-cancelled") as (reached, release):
        cancelled = asyncio.create_task(
            schema.execute(
                _CREATE_CATEGORY,
                variable_values=_create_variables("window-cancelled"),
            ),
        )
        await asyncio.wait_for(reached.wait(), timeout=10)
        cancelled.cancel()
        await asyncio.sleep(0.05)
        cancelled.cancel()
        await asyncio.sleep(0.05)
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await cancelled

    after = await schema.execute(
        _CREATE_CATEGORY,
        variable_values=_create_variables("window-after-cancel"),
    )

    assert after.errors is None
    assert await _committed() == {"window-after-cancel"}


@pytest.mark.django_db(transaction=True)
async def test_work_on_an_outer_thread_sensitive_contexts_thread_never_sees_the_window_open():
    """An outer ``ThreadSensitiveContext`` does not put the window on its thread.

    Django's ASGI handler wraps each request in one, and a consumer may share one
    across a socket's concurrent operations; asgiref's context is re-entrant, so
    an inner one would be a no-op there. Sync work that context runs while the
    window holds its write finds no transaction open on that thread's connection.
    """
    schema = _category_create_schema()
    name = "window-under-an-outer-context"
    with _held_in_the_pipeline(name) as (reached, release):
        async with ThreadSensitiveContext():
            window = asyncio.create_task(
                schema.execute(_CREATE_CATEGORY, variable_values=_create_variables(name)),
            )
            await asyncio.wait_for(reached.wait(), timeout=10)
            sibling = asyncio.create_task(
                sync_to_async(_window_observation, thread_sensitive=True)(),
            )
            await asyncio.sleep(0.05)
            release.set()
            _thread, sibling_in_atomic, _depth = await sibling
            await window

    assert sibling_in_atomic is False


@pytest.mark.django_db(transaction=True)
async def test_a_connection_closed_inside_an_async_window_fails_the_field_and_writes_nothing():
    """A window whose connection a node resolver closed reports an error, never the row.

    The consumer's ``touched`` field runs through Channels' ``database_sync_to_async``
    during completion, whose ``close_old_connections`` closes the window's own
    connection mid-transaction. Django's atomic then skips the commit without
    raising, so the field must resolve as an error, with nothing written.
    """
    schema = _category_create_schema(touched=_touch_through_channels_database_sync_to_async)
    with _connections_really_close():
        result = await schema.execute(
            _CREATE_CATEGORY_TOUCHING,
            variable_values=_create_variables("window-closed-async"),
        )

    assert result.data is None
    assert [(error.message, error.path) for error in result.errors] == [
        (_CLOSED_WINDOW_MESSAGE, ["write0"]),
    ]
    assert await _committed() == set()


@contextlib.contextmanager
def _the_next_off_thread_connect(action):
    """Run ``action`` inside the next connect a thread other than the loop's makes.

    Armed on entry, fired once. ``connection_created`` fires inside Django's
    ``connect()``, which a window's ``atomic.__enter__`` reaches when its thread's
    connection is not open yet - so ``action`` runs, or raises, in the middle of
    that enter, as a slow or failing connect would.
    """
    armed = [True]

    def _on_connect(sender, connection, **kwargs):
        del sender, connection, kwargs
        if armed[0] and threading.current_thread() is not threading.main_thread():
            armed[0] = False
            action()

    connection_created.connect(_on_connect, weak=False)
    try:
        yield
    finally:
        connection_created.disconnect(_on_connect)


@pytest.mark.django_db(transaction=True)
async def test_a_window_cancelled_during_its_enter_still_exits_the_transaction_it_opened():
    """A cancellation landing while ``atomic.__enter__`` runs cannot leave that atomic open.

    The enter cannot be abandoned once its thread started it, so it completes
    after the task was cancelled. The window's exit is queued behind it and runs
    once it finished, so the transaction the enter opened is closed, rolled back,
    and the next mutation commits on its own.
    """
    schema = _category_create_schema()
    loop = asyncio.get_running_loop()
    connecting = asyncio.Event()
    finish_connecting = threading.Event()

    def _slow_connect() -> None:
        loop.call_soon_threadsafe(connecting.set)
        finish_connecting.wait(10)

    with _connections_really_close():
        # A fresh connect on whichever thread the window's enter lands.
        await sync_to_async(lambda: connections["default"].close(), thread_sensitive=True)()
        with _the_next_off_thread_connect(_slow_connect):
            cancelled = asyncio.create_task(
                schema.execute(_CREATE_CATEGORY, variable_values=_create_variables("window-x")),
            )
            await asyncio.wait_for(connecting.wait(), timeout=10)
            cancelled.cancel()
            await asyncio.sleep(0.05)
            finish_connecting.set()
            with pytest.raises(asyncio.CancelledError):
                await cancelled
        after = await schema.execute(
            _CREATE_CATEGORY,
            variable_values=_create_variables("window-after-enter-cancel"),
        )

    assert after.errors is None
    assert await _committed() == {"window-after-enter-cancel"}


@pytest.mark.django_db(transaction=True)
async def test_a_window_whose_transaction_cannot_open_reports_the_failure_and_writes_nothing():
    """A failed enter leaves nothing to exit: the field reports the connect failure."""
    schema = _category_create_schema()

    def _refuse_the_connect() -> None:
        raise DatabaseError("connect refused by the consumer's connection_created receiver")

    with _the_next_off_thread_connect(_refuse_the_connect):
        result = await schema.execute(
            _CREATE_CATEGORY,
            variable_values=_create_variables("window-never-opened"),
        )

    assert [error.message for error in result.errors] == [
        "connect refused by the consumer's connection_created receiver",
    ]
    assert await _committed() == set()


@pytest.mark.django_db
def test_an_async_window_under_a_blocked_sync_caller_nests_in_the_callers_transaction():
    """Under ``async_to_sync`` the window runs on the waiting caller's thread and connection.

    asgiref sends thread-sensitive work to a sync caller blocked in
    ``async_to_sync`` before it consults any context, and that caller's open
    transaction - a test case's, a sync view's - is the one the window must nest
    in: the write is visible to the caller inside it and rolls back with it.
    """
    schema = _category_create_schema()
    with transaction.atomic():
        result = async_to_sync(schema.execute)(
            _CREATE_CATEGORY,
            variable_values=_create_variables("window-nested"),
        )
        seen_inside = product_models.Category.objects.filter(name="window-nested").exists()
        transaction.set_rollback(True)

    assert result.errors is None
    assert seen_inside
    assert not product_models.Category.objects.filter(name="window-nested").exists()


@pytest.mark.django_db(transaction=True)
def test_a_connection_closed_inside_a_sync_window_fails_the_field_and_writes_nothing():
    """The sync mode applies the same closed-connection rule to its calling thread's window."""
    schema = _category_create_schema(touched=_close_old_connections_in_a_resolver)
    with _connections_really_close():
        result = schema.execute_sync(
            _CREATE_CATEGORY_TOUCHING,
            variable_values=_create_variables("window-closed-sync"),
        )

    assert result.data is None
    assert [(error.message, error.path) for error in result.errors] == [
        (_CLOSED_WINDOW_MESSAGE, ["write0"]),
    ]
    with ThreadPoolExecutor(max_workers=1) as reader:
        assert reader.submit(_committed_window_names).result() == set()


@pytest.mark.pg
@pytest.mark.django_db(transaction=True)
async def test_every_success_payload_under_steady_pings_is_a_committed_row():
    """Under a steady ping stream from another socket, no reported write is lost.

    No timing aid: one socket pings continuously while another runs ordinary
    sequential mutations, the production shape in which a real close of a shared
    connection silently discarded committed-looking writes.
    """
    router = _window_router(_category_create_schema())
    names = [f"window-steady-{index}" for index in range(20)]
    stop = asyncio.Event()
    async with _socket(router) as writer, _socket(router) as pinger:

        async def _ping_steadily() -> None:
            while not stop.is_set():
                await pinger.send_json_to({"type": "ping"})
                await pinger.receive_json_from(timeout=10)

        pinging = asyncio.create_task(_ping_steadily())
        try:
            reported = []
            for index, name in enumerate(names):
                await _send_create(writer, name, op_id=str(index))
                reported.append(_reported_name(await _receive_result(writer, op_id=str(index))))
        finally:
            stop.set()
            await pinging

    assert reported == names
    assert await _committed() == set(names)


def test_execution_errors_reads_both_graphql_core_error_shapes():
    """``_execution_errors`` bridges the graphql-core 3.2.9 errors relocation.

    graphql-core < 3.2.9 exposes the located-error list as
    ``ExecutionContext.errors``; 3.2.9 moved it behind a ``CollectedErrors``
    container at ``collected_errors.errors``. The installed version exercises
    only one shape at runtime, so both are pinned here explicitly.
    """
    from django_strawberry_framework.schema import DjangoMutationExecutionContext

    context = object.__new__(DjangoMutationExecutionContext)

    class _Collected:
        errors = ["located"]

    context.collected_errors = _Collected()
    assert context._execution_errors() == ["located"]

    del context.collected_errors
    context.errors = ["legacy"]
    assert context._execution_errors() == ["legacy"]


@pytest.mark.django_db
def test_unmarked_mutation_fields_and_introspection_execute_unwrapped():
    """Consumer-written mutation fields and ``__typename`` skip the transaction wrapper."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation()

    def _plain() -> int:
        return 41

    schema = _mutation_schema(
        UpdateItem,
        extra_fields={"plain": strawberry.mutation(resolver=_plain)},
    )

    result = schema.execute_sync("mutation { __typename plain }")
    assert result.errors is None
    assert result.data == {"__typename": "Mutation", "plain": 41}


# ===========================================================================
# Disappearing rows: forced update / zero-row delete / missing re-fetch -> conflict
# ===========================================================================


class _DeleteTargetOutFromUnder:
    """An authorizing permission class that deletes the located row out-of-band.

    Runs AFTER the locate (the auth seam's position in the pipeline), so the
    located instance's row is gone by the time the write executes - the
    concurrent-delete race, made deterministic. sqlite ignores ``FOR UPDATE``,
    so the default lock cannot serialize the two "transactions" here; on a
    locking backend the same race surfaces only under ``select_for_update=False``.
    """

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        if instance is not None:
            # Stand in for ANOTHER transaction's delete: the phased alias guard
            # polices consumer code (which is read-only pre-save), so the
            # simulated concurrent writer borrows the pipeline's own write-phase
            # seam - the race being made deterministic is the point, not the
            # phase discipline of this fixture.
            with pipeline_write_phase():
                product_models.Item._base_manager.filter(pk=instance.pk).delete()
        return True


@pytest.mark.django_db
def test_update_of_concurrently_deleted_row_returns_conflict_envelope():
    """A forced update matching zero rows is the in-band ``conflict`` envelope, rolled back."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation(permission_classes=[_DeleteTargetOutFromUnder])
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("Vanishing")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "NeverLands"}},
    )

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]
    assert "concurrent" in payload["errors"][0]["messages"][0]
    # The conflict envelope rolled the WHOLE transaction back - including the
    # in-transaction out-of-band delete - and the update was never silently
    # converted into an insert: the row survives with its original name.
    item.refresh_from_db()
    assert item.name == "Vanishing"


@pytest.mark.django_db
def test_delete_of_concurrently_deleted_row_returns_conflict_envelope():
    """A delete whose target row vanished after locate is the ``conflict`` envelope."""
    _declare_item_types()
    DeleteItem = _declare_delete_mutation(permission_classes=[_DeleteTargetOutFromUnder])
    schema = _mutation_schema(DeleteItem)
    item = _seed_item("VanishingDelete")

    result = schema.execute_sync(_DELETE, variable_values={"id": _item_gid(item.pk)})

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]
    assert "concurrent" in payload["errors"][0]["messages"][0]


@pytest.mark.django_db
def test_missing_post_write_refetch_returns_conflict_envelope(monkeypatch):
    """A write whose pk re-fetch finds nothing returns ``conflict``, and rolls back."""
    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("RefetchGone")

    monkeypatch.setattr(mutation_resolvers, "refetch_optimized", lambda *a, **k: None)
    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "RefetchWritten"}},
    )

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]
    item.refresh_from_db()
    assert item.name == "RefetchGone"  # the conflict envelope rolled the write back


# ===========================================================================
# The Django 5.2 / 6.0 zero-row compat disambiguation (unit level)
# ===========================================================================


def test_not_updated_exceptions_prefers_the_typed_signal():
    """Django 6.0's per-model ``NotUpdated`` is caught by type; 5.2 falls back to DatabaseError."""
    typed_signal = getattr(product_models.Item, "NotUpdated", None)
    if typed_signal is not None:
        assert not_updated_exceptions(product_models.Item) == (typed_signal,)
    else:
        # Django < 6.0: models grow no per-model ``NotUpdated``; the helper
        # falls back to the broad ``DatabaseError`` compat catch.
        assert not_updated_exceptions(product_models.Item) == (DatabaseError,)

    class _LegacyModelStandIn:
        """A Django-5.2-shaped model class: no ``NotUpdated`` attribute."""

    assert not_updated_exceptions(_LegacyModelStandIn) == (DatabaseError,)


@pytest.mark.django_db
def test_forced_update_conflict_requires_a_demonstrably_absent_row():
    """A zero-row signal with the row still present re-raises (not a conflict)."""
    item = _seed_item("StillThere")
    signal = DatabaseError("Forced update did not affect any rows.")
    with pytest.raises(DatabaseError):
        forced_update_conflict_errors(item, "default", signal)


@pytest.mark.django_db
def test_forced_update_conflict_maps_absent_row_to_conflict():
    """A zero-row signal with the row demonstrably gone is the ``conflict`` envelope."""
    item = _seed_item("Gone")
    product_models.Item._base_manager.filter(pk=item.pk).delete()
    signal = DatabaseError("Forced update did not affect any rows.")
    errors = forced_update_conflict_errors(item, "default", signal)
    assert [error.field for error in errors] == ["id"]
    assert errors[0].codes == ["conflict"]


@pytest.mark.django_db
def test_forced_update_conflict_requires_a_usable_transaction():
    """With the connection marked needs-rollback the original error propagates untouched."""
    item = _seed_item("Poisoned")
    signal = DatabaseError("some backend failure")
    connection = connections["default"]
    with transaction.atomic():
        connection.needs_rollback = True
        try:
            with pytest.raises(DatabaseError, match="some backend failure"):
                forced_update_conflict_errors(item, "default", signal)
        finally:
            connection.needs_rollback = False


def test_forced_update_conflict_probe_failure_reraises_the_original():
    """The absence probe itself failing re-raises the ORIGINAL error, not the probe's."""
    signal = DatabaseError("the original failure")

    class _ExplodingQuerySet:
        def filter(self, **kwargs):
            return self

        def exists(self):
            raise DatabaseError("probe failure")

    class _ExplodingManager:
        def using(self, alias):
            return _ExplodingQuerySet()

    class _ProbeStandIn:
        """A model-shaped stand-in whose base manager cannot be queried."""

        _base_manager = _ExplodingManager()
        pk = 1

    with pytest.raises(DatabaseError, match="the original failure"):
        forced_update_conflict_errors(_ProbeStandIn(), "default", signal)


def test_conflict_error_shape():
    error = conflict_error()
    assert error.field == "id"
    assert error.codes == ["conflict"]


# ===========================================================================
# Alias pinning: fail-closed hook switch, instance-sensitive router, helpers
# ===========================================================================


@pytest.mark.django_db
def test_visibility_hook_switching_aliases_fails_closed():
    """A ``get_queryset`` hook re-routing to another alias is a loud refusal, not a write."""

    def _reroute(cls, queryset, info, **kwargs):
        return queryset.using("some_other_alias")

    _declare_item_types(item_get_queryset=classmethod(_reroute))
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("PinnedAlias")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "CrossAlias"}},
    )

    assert result.errors is not None
    assert "pinned to alias" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "PinnedAlias"


def test_pin_write_queryset_passes_unrouted_and_matching_querysets():
    queryset = product_models.Item.objects.all()
    assert pin_write_queryset(queryset, "default")._db == "default"
    routed = product_models.Item.objects.using("default")
    assert pin_write_queryset(routed, "default")._db == "default"


def test_pin_write_queryset_derives_the_owner_from_the_model():
    queryset = product_models.Item.objects.using("some_other_alias")
    with pytest.raises(ConfigurationError, match="Item get_queryset"):
        pin_write_queryset(queryset, "default")


def test_check_instance_write_alias_fails_closed_on_divergence(monkeypatch):
    monkeypatch.setattr(
        write_transaction.router,
        "db_for_write",
        lambda model, **hints: "shard_x" if hints.get("instance") is not None else "default",
    )
    with pytest.raises(ConfigurationError, match="instance-sensitive"):
        check_instance_write_alias(product_models.Item, "default", object())
    # A None / matching answer passes.
    monkeypatch.setattr(write_transaction.router, "db_for_write", lambda model, **hints: None)
    check_instance_write_alias(product_models.Item, "default", object())


def test_pipeline_scoped_queryset_is_a_passthrough_on_a_read_surface():
    queryset = product_models.Item.objects.all()
    assert pipeline_scoped_queryset(queryset, product_models.Item) is queryset


def test_pipeline_scoped_queryset_pins_without_locking():
    with write_pipeline("default", lock=False):
        scoped = pipeline_scoped_queryset(
            product_models.Item.objects.all(),
            product_models.Item,
        )
    assert scoped._db == "default"
    assert scoped.query.select_for_update is False


def test_pipeline_scoped_queryset_locks_through_the_base_manager():
    with write_pipeline("default", lock=True):
        scoped = pipeline_scoped_queryset(
            product_models.Item.objects.all(),
            product_models.Item,
        )
    assert scoped._db == "default"
    assert scoped.query.select_for_update is True
    # The lock rides the base manager with visibility reduced to a pk subquery.
    assert "In(Col(" in str(scoped.query.where)


def test_pipeline_scoped_queryset_fails_closed_on_a_cross_alias_queryset():
    with (
        write_pipeline("default", lock=True),
        pytest.raises(ConfigurationError, match="pinned to alias"),
    ):
        pipeline_scoped_queryset(
            product_models.Item.objects.using("some_other_alias"),
            product_models.Item,
        )


def test_resolve_write_alias_model_less_default():
    assert resolve_write_alias(None) == "default"


def test_require_write_pipeline_outside_the_pipeline_is_a_wiring_error():
    with pytest.raises(ConfigurationError, match="outside the write pipeline"):
        require_write_pipeline()
    with write_pipeline("default", lock=False):
        assert require_write_pipeline().alias == "default"


def test_open_write_pipeline_nests_atomic_on_managed_alias():
    """``open_write_pipeline`` opens ``transaction.atomic(using=<managed alias>)``."""
    from unittest.mock import MagicMock, patch

    from django_strawberry_framework.utils.write_transaction import (
        managed_write_transaction,
        open_write_pipeline,
    )

    captured: dict = {}

    class _Atomic:
        def __init__(self, using=None, **_kwargs):
            captured["using"] = using

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    mutation_cls = MagicMock()
    mutation_cls._mutation_meta.select_for_update = False

    with (
        patch(
            "django_strawberry_framework.utils.write_transaction.transaction.atomic",
            side_effect=_Atomic,
        ),
        managed_write_transaction("shard_b"),
    ):
        with open_write_pipeline(mutation_cls) as using:
            assert using == "shard_b"

    assert captured["using"] == "shard_b"


class _FakeBarrierCursor:
    def __init__(self, connection: _FakeBarrierConnection) -> None:
        self._connection = connection
        self._last: tuple | None = None

    def __enter__(self) -> _FakeBarrierCursor:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str) -> None:
        self._connection.executed.append(sql)
        # Model SQLite's connection-level ``PRAGMA query_only`` so the read-back +
        # prior-value-restore + reentrancy behavior is exercised, not just the SQL text.
        if sql == "PRAGMA query_only":
            self._last = (1 if self._connection.query_only else 0,)
        elif sql == "PRAGMA query_only = ON":
            self._connection.query_only = True
        elif sql == "PRAGMA query_only = OFF":
            self._connection.query_only = False

    def fetchone(self) -> tuple | None:
        return self._last


class _FakeBarrierConnection:
    def __init__(self, vendor: str, *, query_only: bool = False) -> None:
        self.vendor = vendor
        self.executed: list[str] = []
        self.query_only = query_only

    def cursor(self) -> _FakeBarrierCursor:
        return _FakeBarrierCursor(self)


def _with_fake_barrier_connection(alias: str, connection: object):
    connections.databases[alias] = dict(connections.databases["default"])
    connections[alias] = connection


def _drop_fake_barrier_connection(alias: str) -> None:
    with contextlib.suppress(AttributeError, KeyError):
        del connections[alias]
    connections.databases.pop(alias, None)


def test_enforce_read_only_barrier_postgresql_sets_transaction_read_only():
    """PostgreSQL is armed with ``SET TRANSACTION READ ONLY``; the mode dies with the txn."""
    connection = _FakeBarrierConnection("postgresql")
    _with_fake_barrier_connection("ro_barrier_pg", connection)
    try:
        disarm = _enforce_read_only_barrier("ro_barrier_pg")
        assert connection.executed == ["SET TRANSACTION READ ONLY"]
        # Disarm is a no-op (nothing to restore on the connection; the read-only mode
        # is scoped to the transaction that is about to be rolled back).
        disarm()
        assert connection.executed == ["SET TRANSACTION READ ONLY"]
    finally:
        _drop_fake_barrier_connection("ro_barrier_pg")


def test_enforce_read_only_barrier_sqlite_arms_and_restores_prior_query_only():
    """SQLite reads the PRIOR ``query_only`` and restores exactly it (never a blind OFF)."""
    connection = _FakeBarrierConnection("sqlite", query_only=False)
    _with_fake_barrier_connection("ro_barrier_sqlite", connection)
    try:
        disarm = _enforce_read_only_barrier("ro_barrier_sqlite")
        # Read prior value first, then arm ON.
        assert connection.executed == ["PRAGMA query_only", "PRAGMA query_only = ON"]
        assert connection.query_only is True
        disarm()
        # Prior was OFF, so restore to OFF.
        assert connection.executed[-1] == "PRAGMA query_only = OFF"
        assert connection.query_only is False
    finally:
        _drop_fake_barrier_connection("ro_barrier_sqlite")


def test_enforce_read_only_barrier_sqlite_preserves_a_preexisting_read_only_flag():
    """A pre-existing ``query_only=ON`` (or an ENCLOSING barrier's arming) survives disarm.

    A blind ``PRAGMA query_only = OFF`` would clobber a pre-existing read-only setting and,
    for nested authorization phases on one connection, an inner disarm would reopen the OUTER
    phase - leaving its guard permitting auth-alias SQL on a now-writable connection.
    """
    connection = _FakeBarrierConnection("sqlite", query_only=True)
    _with_fake_barrier_connection("ro_barrier_sqlite_nested", connection)
    try:
        disarm = _enforce_read_only_barrier("ro_barrier_sqlite_nested")
        assert connection.query_only is True
        disarm()
        # Prior was ON, so the connection stays read-only after disarm.
        assert connection.executed[-1] == "PRAGMA query_only = ON"
        assert connection.query_only is True
    finally:
        _drop_fake_barrier_connection("ro_barrier_sqlite_nested")


def test_enforce_read_only_barrier_fails_closed_on_unsupported_backend():
    """A backend that cannot enforce read-only from an open atomic FAILS CLOSED (no arming)."""
    connection = _FakeBarrierConnection("mysql")
    _with_fake_barrier_connection("ro_barrier_mysql", connection)
    try:
        with pytest.raises(ConfigurationError, match="database-enforced read-only"):
            _enforce_read_only_barrier("ro_barrier_mysql")
        # Fail closed BEFORE issuing any statement on the unsupported connection.
        assert connection.executed == []
    finally:
        _drop_fake_barrier_connection("ro_barrier_mysql")


# ===========================================================================
# Lock opt-out (``Meta.select_for_update = False``) end to end
# ===========================================================================


@pytest.mark.django_db
def test_select_for_update_false_update_still_succeeds_unlocked():
    """The explicit lock opt-out updates cleanly (weaker concurrency, same envelope contract)."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation(select_for_update=False)
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("Unlocked")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "UnlockedUpdated"}},
    )
    assert result.errors is None, result.errors
    assert result.data["write0"]["errors"] == []
    item.refresh_from_db()
    assert item.name == "UnlockedUpdated"


def test_model_flavor_meta_select_for_update_defaults_true_and_rejects_non_bool():
    """The model flavor shares the row-lock validator: default True, non-bool refused."""

    class DefaultLocked(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

    assert DefaultLocked._mutation_meta.select_for_update is True

    with pytest.raises(ConfigurationError, match="select_for_update must be a bool"):

        class BadLock(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "update"
                permission_classes = [_AllowAll]
                select_for_update = "yes"


def test_modelform_flavor_meta_select_for_update_defaults_true():
    from django import forms

    from django_strawberry_framework import DjangoModelFormMutation

    class ItemForm(forms.ModelForm):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class FormUpdate(DjangoModelFormMutation):
        class Meta:
            form_class = ItemForm
            operation = "update"
            permission_classes = [_AllowAll]

    assert FormUpdate._mutation_meta.select_for_update is True


# ===========================================================================
# Strict-boolean authorization
# ===========================================================================


class _TruthyNonBool:
    """A permission class returning a truthy NON-bool (the silent-allow bug shape)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return "yes"


@pytest.mark.django_db
def test_permission_class_returning_non_bool_is_a_configuration_error():
    _declare_item_types()
    UpdateItem = _declare_update_mutation(permission_classes=[_TruthyNonBool])
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("StrictBool")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "Allowed?"}},
    )

    assert result.errors is not None
    assert "must return a bool" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "StrictBool"  # never written


@pytest.mark.django_db
def test_check_permission_override_returning_non_bool_is_a_configuration_error():
    _declare_item_types()

    class NonBoolCheck(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

        def check_permission(
            self,
            info,
            operation,
            data,
            instance=None,
        ):
            return 1  # truthy, not a bool

    schema = _mutation_schema(NonBoolCheck)
    item = _seed_item("StrictCheck")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "Allowed?"}},
    )

    assert result.errors is not None
    assert "check_permission must return a bool" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "StrictCheck"


def test_has_perm_returning_non_bool_is_a_configuration_error():
    from types import SimpleNamespace

    from django_strawberry_framework.mutations.permissions import DjangoModelPermission

    class _WeirdUser:
        is_authenticated = True

        def has_perm(self, codename):
            return "granted"  # truthy, not a bool

    class _Mutation:
        Meta = type("Meta", (), {})

        @classmethod
        def _resolve_model(cls, meta):
            return product_models.Item

    request = SimpleNamespace(user=_WeirdUser())
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    with pytest.raises(ConfigurationError, match="has_perm must return a bool"):
        DjangoModelPermission().has_permission(info, _Mutation, "update", None)


@pytest.mark.django_db
def test_forced_update_integrity_error_race_maps_to_the_constraint_envelope():
    """A forced-update ``IntegrityError`` race is the ``"__all__"`` envelope on update.

    ``IntegrityError`` subclasses ``DatabaseError``, so under the Django 5.2
    untyped zero-row catch the ordering matters: the constraint race must hit
    the ``IntegrityError`` arm, never the conflict disambiguation.
    """
    from unittest import mock

    from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("RaceTarget")

    with mock.patch.object(
        product_models.Item,
        "save",
        side_effect=IntegrityError("races validate_constraints"),
    ):
        result = schema.execute_sync(
            _UPDATE,
            variable_values={"id": _item_gid(item.pk), "d": {"name": "Raced"}},
        )

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert payload["errors"][0]["field"] == NON_FIELD_ERROR_KEY
    assert payload["errors"][0]["messages"] == ["A database constraint was violated."]
    item.refresh_from_db()
    assert item.name == "RaceTarget"


# ---------------------------------------------------------------------------
# The phased alias guard + canonical pk equality + target-state drift (hardening)
# ---------------------------------------------------------------------------


def test_is_read_only_sql_uses_a_comment_stripped_allow_list():
    """Read-only classification is an ALLOW-list over the first comment-stripped token."""
    from django_strawberry_framework.utils.write_transaction import is_read_only_sql

    assert is_read_only_sql("SELECT 1")
    assert is_read_only_sql("(SELECT 1)")
    assert is_read_only_sql("((SELECT 1))")
    assert is_read_only_sql("SELECT(1)")
    assert is_read_only_sql("SELECT* FROM t")
    assert is_read_only_sql("  /* lead */ -- note\n select name from t")
    assert is_read_only_sql('SAVEPOINT "s1"')
    assert is_read_only_sql('RELEASE SAVEPOINT "s1"')
    assert is_read_only_sql('ROLLBACK TO SAVEPOINT "s1"')
    # Writes, DDL, EXPLAIN (PostgreSQL EXPLAIN ANALYZE executes), and CTE openers
    # (a data-modifying CTE writes through a read-shaped opener) are all rejected.
    assert not is_read_only_sql("INSERT INTO t VALUES (1)")
    assert not is_read_only_sql("(INSERT INTO t VALUES (1))")
    assert not is_read_only_sql("/* comment */ UPDATE t SET x = 1")
    assert not is_read_only_sql("(UPDATE t SET x = 1)")
    assert not is_read_only_sql("EXPLAIN ANALYZE UPDATE t SET x = 1")
    assert not is_read_only_sql("WITH d AS (DELETE FROM t RETURNING 1) SELECT * FROM d")
    # Degenerate shapes fail CLOSED: comment-only / unterminated-comment / empty.
    assert not is_read_only_sql("-- only a comment")
    assert not is_read_only_sql("/* unterminated")
    assert not is_read_only_sql("")


def test_is_read_only_sql_uses_base_string_content_for_subclasses():
    """A string subclass cannot disguise write SQL as an allowed read token."""
    from django_strawberry_framework.utils.write_transaction import is_read_only_sql

    class DisguisedWriteSQL(str):
        def __getitem__(self, key):
            if isinstance(key, slice):
                return "SELECT 1"
            return str.__getitem__("SELECT 1", key)

    sql = DisguisedWriteSQL("DELETE FROM protected_rows")
    assert not is_read_only_sql(sql)


def test_is_read_only_sql_fails_closed_on_a_non_string_statement():
    """A statement the classifier cannot read is never read-only, and reading it raises nothing.

    ``cursor.execute`` hands the guard whatever object the caller passed. A non-string
    whose ``__str__`` detonates must not escape the phase guard as a raw exception: an
    unreadable statement is unclassifiable, and the only honest verdict for the
    read-only phase is "not provably read-only" (fail closed).
    """
    from django_strawberry_framework.utils.write_transaction import is_read_only_sql

    class _HostileStr:
        def __str__(self):
            raise RuntimeError("hostile __str__")

    assert is_read_only_sql(_HostileStr()) is False
    assert is_read_only_sql(None) is False
    assert is_read_only_sql(b"SELECT 1") is False  # bytes SQL is not DB-API either


@pytest.mark.django_db
def test_pinned_alias_guard_rejects_writes_outside_the_write_phase():
    """On the PINNED alias, write SQL is rejected in the read-only phase and allowed inside it."""
    from django.db import connection

    from django_strawberry_framework.utils.write_transaction import (
        pipeline_alias_guard,
        pipeline_write_phase,
        write_pipeline,
    )

    with write_pipeline("default", lock=False), pipeline_alias_guard("GuardMut", "default"):
        # Reads pass in the read-only phase.
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        # Write SQL outside the write phase fails closed. (Contained in a
        # savepoint so the rejection does not mark the TEST transaction broken -
        # in the real pipeline the error propagates and rolls the mutation back.)
        with pytest.raises(ConfigurationError, match="OUTSIDE the mutation's write phase"):
            with transaction.atomic():
                product_models.Category.objects.create(name="PhaseCat")
        assert not product_models.Category.objects.filter(name="PhaseCat").exists()
        # The SAME statement inside the write phase succeeds.
        with pipeline_write_phase():
            product_models.Category.objects.create(name="PhaseCat")
        assert product_models.Category.objects.filter(name="PhaseCat").exists()


def test_pks_match_canonicalizes_through_the_pk_field():
    """pk equality goes through the model pk field's ``to_python``, failing closed on garbage."""
    import uuid
    from types import SimpleNamespace

    from django.db import models as django_models

    from django_strawberry_framework.utils.write_transaction import canonical_pk, pks_match

    uuid_model = SimpleNamespace(_meta=SimpleNamespace(pk=django_models.UUIDField()))
    value = uuid.uuid4()
    # The SAME row under three spellings: UUID object, dashed, un-dashed.
    assert pks_match(uuid_model, value, str(value))
    assert pks_match(uuid_model, value, value.hex)
    assert not pks_match(uuid_model, value, uuid.uuid4())
    # A forged pk of the wrong shape is a MISMATCH, never an exception.
    assert not pks_match(uuid_model, value, "not-a-uuid")

    int_model = SimpleNamespace(_meta=SimpleNamespace(pk=django_models.IntegerField()))
    assert pks_match(int_model, 5, "5")
    assert canonical_pk(int_model, "7") == 7


def test_reject_substituted_row_is_silent_when_pks_match():
    from types import SimpleNamespace

    from django.db import models as django_models

    from django_strawberry_framework.utils.write_transaction import reject_substituted_row

    model = SimpleNamespace(_meta=SimpleNamespace(pk=django_models.IntegerField()))
    reject_substituted_row(model, 5, "5", message="unused")


def test_reject_substituted_row_raises_the_caller_message():
    from types import SimpleNamespace

    from django.db import models as django_models

    from django_strawberry_framework.utils.write_transaction import reject_substituted_row

    model = SimpleNamespace(_meta=SimpleNamespace(pk=django_models.IntegerField()))
    with pytest.raises(ConfigurationError, match="never a substituted one"):
        reject_substituted_row(model, 1, 2, message="never a substituted one")


@pytest.mark.django_db
def test_target_state_snapshot_and_drift_rejection():
    """``assert_no_target_drift`` rejects mutated loaded fields; deferred fields never read as drift."""
    from django_strawberry_framework.utils.write_transaction import (
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    category = product_models.Category.objects.create(name="DriftHelperCat")
    item = product_models.Item.objects.create(name="DriftHelperItem", category=category)

    with write_pipeline("default", lock=False):
        pipeline = require_write_pipeline()
        # No snapshot recorded (a direct skeleton-less call): the check is a no-op.
        assert_no_target_drift("NoSnapshotMut", item)

        pipeline.target_state = snapshot_target_state(item)
        assert_no_target_drift("CleanMut", item)  # unchanged: no raise

        item.name = "drifted"
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("DriftMut", item)

    # A DEFERRED field is absent from the snapshot and skipped by the check.
    deferred_item = product_models.Item.objects.defer("description").get(pk=item.pk)
    with write_pipeline("default", lock=False):
        pipeline = require_write_pipeline()
        pipeline.target_state = snapshot_target_state(deferred_item)
        assert "description" not in pipeline.target_state
        assert_no_target_drift("DeferredMut", deferred_item)  # no lazy-load, no raise

        # And the converse: a field SNAPSHOTTED loaded but deferred at CHECK time is
        # skipped too (comparing it would lazy-load - the check must never query).
        item.refresh_from_db()
        pipeline.target_state = snapshot_target_state(item)
        assert "description" in pipeline.target_state
        assert_no_target_drift("DeferredAtCheckMut", deferred_item)  # skip, no raise


@pytest.mark.django_db
def test_snapshot_target_state_fingerprints_mutable_container_values():
    """A JSONField / ArrayField value is fingerprinted, so in-place mutation reads as drift."""
    from types import SimpleNamespace

    from django_strawberry_framework.utils.write_transaction import (
        _FieldFingerprint,
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    field = SimpleNamespace(attname="payload")
    instance = SimpleNamespace(
        payload={"tier": "gold", "tags": ["a"]},
        _meta=SimpleNamespace(concrete_fields=[field]),
        get_deferred_fields=lambda: set(),
    )

    snapshot = snapshot_target_state(instance)
    # Captured as a structural fingerprint independent of the live container.
    assert isinstance(snapshot["payload"], _FieldFingerprint)

    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot
        # An unchanged value re-fingerprints identically: no drift.
        assert_no_target_drift("JsonCleanMut", instance)
        # Mutating the JSON value IN PLACE - a by-reference snapshot would alias
        # the very object being mutated and miss this; the fingerprint catches it.
        instance.payload["tier"] = "platinum"
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("JsonDriftMut", instance)
        # A value that cannot be RE-fingerprinted at all (a reference cycle
        # planted after the capture) still fails closed with the typed pipeline
        # error - never a raw exception, and never a silent pass.
        instance.payload["self"] = instance.payload
        with pytest.raises(ConfigurationError, match="reference cycle"):
            assert_no_target_drift("JsonCycleMut", instance)


def test_snapshot_target_state_captures_filefield_name_not_the_mutable_descriptor():
    """A FieldFile is snapshotted by its ``name``: an in-place name re-point reads as drift.

    ``FieldFile`` is a MUTABLE descriptor - a hook can assign ``instance.<file>.name`` on the
    SAME object, so a by-reference snapshot would alias it and the identity/``==`` check would
    miss the unauthorized file-column change. Snapshotting the ``name`` catches it.
    """
    from types import SimpleNamespace

    from django.db.models.fields.files import FieldFile

    from django_strawberry_framework.utils.write_transaction import (
        _FileNameSnapshot,
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    fake_field = SimpleNamespace(storage=None, attname="avatar")
    file_value = FieldFile(instance=None, field=fake_field, name="orig.png")
    field = SimpleNamespace(attname="avatar")
    instance = SimpleNamespace(
        avatar=file_value,
        _meta=SimpleNamespace(concrete_fields=[field]),
        get_deferred_fields=lambda: set(),
    )

    snapshot = snapshot_target_state(instance)
    # Captured by its DB-relevant name string, NOT the mutable descriptor object.
    assert isinstance(snapshot["avatar"], _FileNameSnapshot)
    assert snapshot["avatar"].name == "orig.png"

    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot
        assert_no_target_drift("FileCleanMut", instance)  # unchanged: no raise
        # Re-point the FieldFile name IN PLACE (same object) - the identity/== path a
        # by-reference snapshot uses would miss this; the name snapshot catches it.
        instance.avatar.name = "evil.png"
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("FileDriftMut", instance)


@pytest.mark.django_db
def test_assert_no_target_drift_fails_closed_on_a_hostile_eq():
    """A planted value whose equality read detonates is the typed envelope, never raw.

    The code the drift check polices (a permission method / hook / validator) can
    plant ANY object on a field - including one whose ``__eq__`` raises. An
    unreadable comparison is drift the check cannot rule out, so it fails closed
    into the typed ``ConfigurationError``; a raw escape would break the pipeline's
    exception-containment contract.
    """
    from django_strawberry_framework.utils.write_transaction import (
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    class _RaisingEq:
        def __eq__(self, other):
            raise RuntimeError("hostile __eq__")

        def __hash__(self):
            return 0

    category = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="GuardEq", category=category)
    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot_target_state(item)
        item.name = _RaisingEq()  # planted by the code the check polices
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("GuardEqMut", item)


def test_file_name_snapshot_fails_closed_on_a_hostile_replacement():
    """A non-``FieldFile`` replacement with a hostile ``__eq__`` reads as drift, not a raw escape.

    The name snapshot compares the replaced value raw when it is not a
    ``FieldFile`` - and a hostile replacement's equality read detonating must
    answer "drifted" (fail closed), never propagate out of the guard.
    """
    from types import SimpleNamespace

    from django.db.models.fields.files import FieldFile

    from django_strawberry_framework.utils.write_transaction import (
        _FileNameSnapshot,
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    class _RaisingEq:
        def __eq__(self, other):
            raise RuntimeError("hostile __eq__")

        def __hash__(self):
            return 0

    fake_field = SimpleNamespace(storage=None, attname="avatar")
    file_value = FieldFile(instance=None, field=fake_field, name="orig.png")
    field = SimpleNamespace(attname="avatar")
    instance = SimpleNamespace(
        avatar=file_value,
        _meta=SimpleNamespace(concrete_fields=[field]),
        get_deferred_fields=lambda: set(),
    )

    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot_target_state(instance)
        assert isinstance(require_write_pipeline().target_state["avatar"], _FileNameSnapshot)
        instance.avatar = _RaisingEq()  # replaced with a hostile non-FieldFile
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("GuardFileMut", instance)


@pytest.mark.django_db
def test_snapshot_fingerprint_is_iterative_and_budgeted():
    """A pathologically DEEP field value fingerprints without RecursionError (iterative)."""
    from types import SimpleNamespace

    from django_strawberry_framework.utils.write_transaction import (
        _SNAPSHOT_NODE_BUDGET,
        _field_fingerprint,
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    # Deeper than Python's default recursion limit - copy.deepcopy / recursive
    # comparison would raise RecursionError; the iterative fingerprint does not.
    deep: dict = {}
    node = deep
    for _ in range(5000):
        child: dict = {}
        node["next"] = child
        node = child
    node["leaf"] = 1

    field = SimpleNamespace(attname="payload")
    instance = SimpleNamespace(
        payload=deep,
        _meta=SimpleNamespace(concrete_fields=[field]),
        get_deferred_fields=lambda: set(),
    )
    snapshot = snapshot_target_state(instance)  # no RecursionError
    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot
        assert_no_target_drift("DeepCleanMut", instance)  # unchanged: no raise
        node["leaf"] = 2  # mutate the deepest scalar in place
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("DeepDriftMut", instance)

    # A value exceeding the node budget is rejected loudly, never walked unbounded.
    with pytest.raises(ConfigurationError, match="too large to fingerprint"):
        _field_fingerprint(list(range(_SNAPSHOT_NODE_BUDGET + 2)))


def test_field_fingerprint_covers_container_kinds_and_is_deterministic():
    """The fingerprint handles set / frozenset / bytes / tuple and is order-stable per structure."""
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    # Sets/frozensets fingerprint by a deterministic (repr-sorted) member order,
    # so equal sets built in different insertion orders match.
    assert _field_fingerprint({3, 1, 2}) == _field_fingerprint({2, 3, 1})
    assert _field_fingerprint(frozenset({"b", "a"})) == _field_fingerprint(frozenset({"a", "b"}))
    # Dicts fingerprint by sorted keys; lists/tuples keep order.
    assert _field_fingerprint({"a": 1, "b": 2}) == _field_fingerprint({"b": 2, "a": 1})
    assert _field_fingerprint([1, 2, 3]) != _field_fingerprint([3, 2, 1])
    # bytes / bytearray are captured by value; a change in content changes the digest.
    assert _field_fingerprint(b"abc") == _field_fingerprint(bytearray(b"abc"))
    assert _field_fingerprint(b"abc") != _field_fingerprint(b"abd")
    # Scalars are type-tagged: 1 and "1" never collide.
    assert _field_fingerprint([1]) != _field_fingerprint(["1"])
    # A nested mix round-trips stably.
    value = {"tags": [1, 2], "meta": {"seen": True}, "ids": {9, 8}}
    assert _field_fingerprint(value) == _field_fingerprint(dict(value))


def test_field_fingerprint_reads_hostile_containers_through_their_base_slots():
    """A container SUBCLASS cannot decide what the drift fingerprint sees.

    The fingerprint is one half of a security check whose other half recomputes
    it later, so a value that reports different contents on different calls
    would let an unauthorized in-memory change compare clean. The walk therefore
    reads every built-in container through its UNBOUND slot, and a lying
    ``__iter__`` / ``__reversed__`` never runs.
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    class _LyingList(list):
        def __iter__(self):
            return iter([999])

        def __reversed__(self):
            return iter([999])

    class _LyingDict(dict):
        def items(self):
            return iter([("spoofed", 999)])

        def keys(self):
            return iter(["spoofed"])

    assert _field_fingerprint(_LyingList([1, 2, 3])) == _field_fingerprint([1, 2, 3])
    assert _field_fingerprint(_LyingDict({"a": 1})) == _field_fingerprint({"a": 1})


def test_field_fingerprint_orders_by_a_guarded_key_not_a_bare_repr():
    """A constant or raising ``__repr__`` cannot collapse or break the ordering.

    A bare ``repr`` sort key is two failures in one: a ``__repr__`` that raises
    escapes the drift check as an untyped exception, and one that returns a
    CONSTANT gives structurally different members the same sort key - which, for
    an unordered container, means two different values can fingerprint the same
    and drift between them goes undetected.
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    class _ConstantRepr:
        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return "SAME"

    class _RaisingRepr:
        def __repr__(self):
            raise RuntimeError("hostile repr")

    # No raise, and the guarded placeholder still names the type.
    digest = _field_fingerprint([_RaisingRepr()])
    assert "_RaisingRepr" in digest

    # A constant repr no longer makes two distinct members interchangeable: the
    # ordering key falls through to type and object identity, which are total.
    first, second = _ConstantRepr(1), _ConstantRepr(2)
    assert _field_fingerprint({first: "x", second: "y"}) == _field_fingerprint(
        {first: "x", second: "y"},
    )


def test_field_fingerprint_rejects_a_reference_cycle():
    """A self-referential value is rejected by name, not by exhausting the node budget.

    Consumer code between the locate and the save can make a JSONField value
    cyclic; the drift check then recomputes the fingerprint over it. The node
    budget already bounded the walk, but it reported the wrong reason - an
    active-path guard names the actual defect.
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    cyclic: dict = {}
    cyclic["self"] = cyclic
    with pytest.raises(ConfigurationError, match="reference cycle"):
        _field_fingerprint(cyclic)

    nested: list = [1]
    nested.append(nested)
    with pytest.raises(ConfigurationError, match="reference cycle"):
        _field_fingerprint(nested)


def test_field_fingerprint_admits_a_repeated_sibling_that_is_not_a_cycle():
    """The guard tracks the ACTIVE PATH, so a diamond is fine and only a cycle raises."""
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    shared = {"a": 1}
    assert _field_fingerprint([shared, shared]) == _field_fingerprint([{"a": 1}, {"a": 1}])


def test_field_fingerprint_reads_atom_leaves_through_base_slots():
    """A scalar subclass's lying ``__repr__`` cannot forge another value's leaf.

    The write persists a leaf's BASE content (``json.dumps`` serializes the base
    string of a ``str`` subclass, never its ``__repr__``), so a leaf that trusted
    the subclass's repr would let a smuggled value fingerprint as the value it
    CLAIMS to be - a fail-open drift check. The walk renders every built-in atom
    through its BASE type's unbound slot and tags the leaf by that base type,
    never by the subclass's claimed ``__name__``; content-equal replacements
    stay honest (no false drift).
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    shadow_str = type("str", (str,), {"__repr__": lambda self: repr("gold")})
    shadow_int = type("int", (int,), {"__repr__": lambda self: "10"})

    # Different base content -> different digest, however loudly the repr lies.
    assert _field_fingerprint(["gold"]) != _field_fingerprint([shadow_str("admin")])
    assert _field_fingerprint({10: 1}) != _field_fingerprint({shadow_int(20): 1})
    # Equal base content -> equal digest: the fingerprint is content-honest.
    assert _field_fingerprint(["gold"]) == _field_fingerprint([shadow_str("gold")])


def test_field_fingerprint_reads_bytes_through_their_base_buffer():
    """A ``bytes`` / ``bytearray`` subclass's raising ``__bytes__`` never runs.

    The byte-string leaf is read through the base buffer, never ``bytes(item)``
    (the constructor dispatches a subclass ``__bytes__``), and it stays
    content-addressed and type-insensitive.
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    class _RaisingBytes(bytes):
        def __bytes__(self):
            raise RuntimeError("hostile __bytes__")

    class _RaisingBytearray(bytearray):
        def __bytes__(self):
            raise RuntimeError("hostile bytearray __bytes__")

    assert _field_fingerprint([_RaisingBytes(b"secret")]) == _field_fingerprint([b"secret"])
    assert _field_fingerprint([_RaisingBytearray(b"secret")]) == _field_fingerprint([b"secret"])
    assert _field_fingerprint([b"secret"]) != _field_fingerprint([b"tampered"])


def test_field_fingerprint_distinguishes_opaque_objects_a_constant_repr_cannot_collapse():
    """Two distinct opaque objects with one constant ``__repr__`` fingerprint apart.

    A total ORDERING key alone is not enough: the LEAF must not render two
    distinct objects equal either, or a replaced value with a lying constant
    repr would compare clean against the captured digest (fail-open). Opaque
    leaves therefore carry the type's and the value's identity alongside the
    guarded repr - sound because a fingerprint is request-scoped (recomputed
    from the same live objects, never persisted).
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    class _ConstantRepr:
        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return "SAME"

    first, second = _ConstantRepr(1), _ConstantRepr(2)
    assert _field_fingerprint([first, "x"]) != _field_fingerprint([second, "x"])
    # Re-fingerprinting the SAME objects is stable (the drift check's shape).
    assert _field_fingerprint([first, "x"]) == _field_fingerprint([first, "x"])


def test_field_fingerprint_walks_dict_keys_as_nodes():
    """A dict key gets the same hostile-safe walk as a value, never a ``repr`` label.

    A ``repr`` key label is a second place a lying ``__repr__`` could forge the
    fingerprint (a shadowed-int key claiming another key's spelling); walking
    the key as a node routes it through the same base-slot leaf render a value
    gets, including container keys (tuples / frozensets are hashable).
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    # Container keys are walked by content, not rendered by ``repr``.
    assert _field_fingerprint({(1, 2): "a"}) != _field_fingerprint({(1, 3): "a"})
    assert _field_fingerprint({(1, 2): "a"}) == _field_fingerprint({(1, 2): "a"})
    # The fixed key/value divider keeps the two roles distinguishable.
    assert _field_fingerprint({10: "x"}) != _field_fingerprint({"x": 10})


def test_field_fingerprint_leaf_tokens_stay_type_tagged():
    """None / bool / float leaves keep their own type tags - 1, True, 1.0, and '1' never collide.

    The atom tags come from the base type that performed the content read, so a
    bool (an ``int`` subclass) and a float cannot masquerade as one another and
    an explicit ``None`` never reads as the string ``"None"``.
    """
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    assert _field_fingerprint([None]) != _field_fingerprint(["None"])
    assert _field_fingerprint([None]) == _field_fingerprint([None])  # stable
    assert _field_fingerprint([True]) != _field_fingerprint([1])
    assert _field_fingerprint([1.5]) != _field_fingerprint(["1.5"])
    assert _field_fingerprint([1.5]) != _field_fingerprint([15])
