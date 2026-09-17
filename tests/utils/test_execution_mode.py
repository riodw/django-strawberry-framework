"""``utils/execution_mode.py`` - which GraphQL executor is driving this resolver.

The fact a field factory has to have before it decides what to hand back, and
the one question the ambient event loop is not allowed to answer. The rows here
drive the readers directly, because the disagreement they exist for is invisible
from either surface on its own: ``execute_sync`` and ``await schema.execute``
each look correct until a synchronous operation is started from inside an
asynchronous one, and then the loop says "async" while the synchronous executor
holds the operation.

What the readers are worth to a field is ``tests/test_list_field.py``'s
three-state matrix, and live in
``examples/fakeshop/test_query/test_list_field_async_api.py``. How long the
binding lives - across nesting, streamed frames, copied contexts and teardown -
is ``tests/extensions/test_operation_state.py``.
"""

from __future__ import annotations

import pytest
import strawberry

from django_strawberry_framework import DjangoSchema, SyncMisuseError
from django_strawberry_framework.utils.execution_mode import (
    OperationMode,
    async_execution,
    current_operation_mode,
    operation_is_async,
)


@strawberry.type
class _Query:
    """A schema whose one field reports what the readers answer inside it."""

    @strawberry.field
    def readings(self) -> str:
        """``mode|operation_is_async()|async_execution()``, as the operation sees them."""
        return f"{current_operation_mode()}|{operation_is_async()}|{async_execution()}"

    @strawberry.field
    def fact(self) -> str:
        """Only the reader that never refuses, for the case where the other does."""
        return f"{current_operation_mode()}|{operation_is_async()}"


def _schema() -> DjangoSchema:
    return DjangoSchema(query=_Query)


def test_nothing_is_bound_outside_every_operation():
    """The readers answer for no operation where no runner owns one.

    Not a default of "sync": a caller outside an operation is not inside an
    operation of either color, and a reader that guessed one would give a
    resolver in a background task an answer about an operation that has ended.
    """
    assert current_operation_mode() is None


def test_a_synchronous_operation_is_synchronous_all_the_way_down():
    """``execute_sync`` is the one entry point that declares the synchronous executor."""
    assert _schema().execute_sync("{ readings }").data == {
        "readings": "OperationMode.SYNC|False|False",
    }


@pytest.mark.asyncio
async def test_an_awaited_operation_is_asynchronous_all_the_way_down():
    """``execute`` leaves upstream's ``sync`` flag false, and the chain says so."""
    result = await _schema().execute("{ readings }")

    assert result.data == {"readings": "OperationMode.ASYNC|True|True"}


@pytest.mark.asyncio
async def test_a_streamed_operation_is_asynchronous_too():
    """``stream`` and ``subscribe`` come through the same flag as ``execute``."""
    stream = await _schema().stream("{ readings }")
    frames = [frame async for frame in stream]

    assert [frame.data for frame in frames] == [{"readings": "OperationMode.ASYNC|True|True"}]


@pytest.mark.asyncio
async def test_a_synchronous_operation_inside_a_running_loop_stays_synchronous():
    """The disagreement, read at the seam that owns it.

    ``Schema.execute_sync`` is callable while an event loop is running - most
    directly from a resolver inside an asynchronous operation - so on that path
    the loop is running while the synchronous executor holds the operation. The
    mode is the entry point's and does not change; the reader that has to choose
    a return value refuses instead of guessing, and the reader that only states
    the fact still states it.
    """
    schema = _schema()

    assert schema.execute_sync("{ fact }").data == {"fact": "OperationMode.SYNC|False"}

    refused = schema.execute_sync("{ readings }")

    assert refused.data is None
    assert isinstance(refused.errors[0].original_error, SyncMisuseError)
    assert "await schema.execute" in str(refused.errors[0])
    assert "worker thread" in str(refused.errors[0])


@pytest.mark.asyncio
async def test_a_plain_strawberry_schema_falls_back_to_the_ambient_loop():
    """Nothing binds a mode there, and nothing pretends one was bound.

    A plain ``strawberry.Schema`` never creates the package runner, so both
    readers answer from the loop exactly as upstream leaves them - the
    disagreement included, which stays reachable on that schema.
    ``DjangoSchema`` is the spelling that makes the mode authoritative, and this
    row is what makes the fallback a stated boundary rather than an accident.
    """
    plain = strawberry.Schema(query=_Query)

    assert plain.execute_sync("{ readings }").data == {"readings": "None|True|True"}
    assert (await plain.execute("{ readings }")).data == {"readings": "None|True|True"}


def test_a_plain_strawberry_schema_outside_a_loop_reads_the_loop_it_has():
    """The other half of the fallback: no loop, no mode, and a synchronous answer."""
    plain = strawberry.Schema(query=_Query)

    assert plain.execute_sync("{ readings }").data == {"readings": "None|False|False"}


def test_the_two_modes_are_distinct_members():
    """The enum is the one definition of execution color both readers derive from."""
    assert OperationMode.SYNC is not OperationMode.ASYNC
    assert {mode.value for mode in OperationMode} == {"sync", "async"}
