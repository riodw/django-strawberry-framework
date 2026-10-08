"""Hostile-input containment for the WebSocket consumer.

Package-tier because fakeshop has no ``config/asgi.py`` and no WebSocket
mount: a live ``/graphql/`` HTTP request cannot present a Channels scope,
drive ``WebsocketCommunicator``, or reach either actor-revalidation
checkpoint. That fixture gap is recorded with ``tests/test_routers.py`` in
``examples/fakeshop/test_query/README.md``; this file does not add the mount.

What a live HTTP request cannot express, and what therefore stays here:

- hostile-input containment on ``_actor_is_current``,
  ``revalidate_operation_actor``, ``send_revalidated_operation_frame``,
  the revocation-gated adapter, and ``_revoke_connection`` (fail-closed;
  ``CancelledError`` re-raised);
- construction-time ``resolved_revalidation_window`` (pure function;
  ``tests/test_routers.py`` drives the same domain through router
  construction);
- ``_host_validation_request`` projection shape (handshake verdicts live
  in ``tests/test_routers.py`` via ``WebsocketCommunicator``);
- hostile ``connection_actor_state`` mapping/isinstance containment used
  by those checkpoints (happy-path lease lifecycle is
  ``tests/utils/test_sessions.py``).

The HTTP transport boundary is earned over fakeshop's real ``/graphql/``
in ``examples/fakeshop/test_query/test_transport_api.py``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Protocol
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typing_extensions import override

from django_strawberry_framework import consumers as cmod
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.sessions import (
    _ACTOR_STATE_SCOPE_KEY,
    ConnectionActorState,
    connection_actor_state,
)
from tests._idioms import websocket_scope

if TYPE_CHECKING:
    from django_strawberry_framework.consumers import RevalidatingGraphQLWSConsumer


def _fresh_scope():
    scope: dict[str, object] = {}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    return scope


# ---------------------------------------------------------------------------
# utils/sessions - hostile scope containment (owning layer)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc_type",
    [pytest.param(TypeError, id="type-error"), pytest.param(ValueError, id="value-error")],
)
def test_connection_actor_state_hostile_get_raises_configuration_error(exc_type: type[Exception]):
    """A raising ``scope.get`` becomes ``ConfigurationError``, chained to the cause."""

    class HostileScope(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            raise exc_type("hostile get")

    with pytest.raises(ConfigurationError) as excinfo:
        connection_actor_state(HostileScope())
    assert excinfo.value.__cause__ is not None
    assert isinstance(excinfo.value.__cause__, exc_type)


def test_connection_actor_state_hostile_setitem_raises_configuration_error():
    class HostileScope(dict[str, object]):
        @override
        def __setitem__(self, k: str, v: object):
            raise ValueError("hostile set")

    with pytest.raises(ConfigurationError) as excinfo:
        connection_actor_state(HostileScope())
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_connection_actor_state_corrupted_value_raises_configuration_error():
    scope: dict[str, object] = {_ACTOR_STATE_SCOPE_KEY: "not-a-state"}
    with pytest.raises(ConfigurationError, match="corrupted"):
        connection_actor_state(scope)


# ---------------------------------------------------------------------------
# consumers._actor_is_current - hostile containment (fail-closed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc_type",
    [pytest.param(TypeError, id="type-error"), pytest.param(ValueError, id="value-error")],
)
async def test_actor_is_current_hostile_scope_get_fails_closed(exc_type: type[Exception]):
    """A raising ``scope.get('user')`` fails closed rather than escaping."""

    class HostileScope(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            if k == "user":
                raise exc_type("hostile get user")
            return super().get(k, d)

    scope = HostileScope()
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    result = await cmod._actor_is_current(consumer)
    assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_is_authenticated_treated_as_anon_when_never_authed():
    class HostileUser:
        @property
        def is_authenticated(self):
            raise ValueError("hostile is_auth")

    scope: dict[str, object] = {"user": HostileUser()}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    result = await cmod._actor_is_current(consumer)
    # never authed -> anon carve-out allows
    assert result is True


@pytest.mark.asyncio
async def test_actor_is_current_hostile_is_authenticated_denies_when_previously_authed():
    class HostileUser:
        @property
        def is_authenticated(self):
            raise ValueError("hostile is_auth")

    scope: dict[str, object] = {"user": HostileUser()}
    st = ConnectionActorState()
    st.authenticated_provenance = True
    scope[_ACTOR_STATE_SCOPE_KEY] = st
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    result = await cmod._actor_is_current(consumer)
    assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_connection_was_authenticated_fails_closed():
    class HostileScope(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            if k == _ACTOR_STATE_SCOPE_KEY:
                raise KeyError("hostile actor state")
            if k == "user":
                return None
            return super().get(k, d)

    scope = HostileScope()
    # need to have user=None to hit the anon carve-out
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    result = await cmod._actor_is_current(consumer)
    assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_note_authenticated_actor_fails_closed():
    scope2: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope2[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope2
    consumer.revalidation_window = 0.0
    with patch(
        "django_strawberry_framework.consumers.note_authenticated_actor",
        side_effect=AttributeError("hostile note"),
    ):
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_window_attribute_fails_closed():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    # hostile property for revalidation_window
    type(consumer).revalidation_window = property(
        lambda self: (_ for _ in ()).throw(AttributeError("hostile window")),
    )

    # Actually Mock property trick is messy; use a real object with hostile property
    class HostileConsumer:
        @property
        def revalidation_window(self):
            raise AttributeError("hostile window")

        @property
        def scope(self):
            return scope

    hc = HostileConsumer()
    # basedpyright: the consumer whose revalidation_window read raises is the hostile input under
    # test; _actor_is_current types the parameter as _RevalidatedConsumer
    result = await cmod._actor_is_current(hc)  # pyright: ignore[reportArgumentType]
    assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_window_comparison_falls_through_to_db():
    class HostileFloat:
        def __gt__(self, other: object):
            raise AttributeError("hostile gt")

    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    actor_state = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY] = actor_state
    actor_state.authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = HostileFloat()
    # _refreshed_actor will be called; mock it to succeed
    with patch.object(cmod, "_refreshed_actor", new_callable=AsyncMock) as mock_ref:
        mock_ref.return_value = Mock(is_authenticated=True)
        result = await cmod._actor_is_current(consumer)
        # hostile comparison should not authorize from cache; it falls through
        # to DB which we mocked to succeed, so it should be True (since DB says authed)
        # but we also need to handle the scope write
        assert result is True
        mock_ref.assert_awaited_once()


@pytest.mark.asyncio
async def test_actor_is_current_hostile_revalidated_at_get_falls_through():
    class HostileScope(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            if k == cmod._REVALIDATED_AT_SCOPE_KEY:
                raise IndexError("hostile revalidated get")
            if k == "user":
                return Mock(is_authenticated=True)
            return super().get(k, d)

    scope = HostileScope()
    actor_state = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY] = actor_state
    actor_state.authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 10.0
    with patch.object(cmod, "_refreshed_actor", new_callable=AsyncMock) as mock_ref:
        mock_ref.return_value = Mock(is_authenticated=True)
        result = await cmod._actor_is_current(consumer)
        assert result is True


@pytest.mark.asyncio
async def test_actor_is_current_hostile_refreshed_actor_fails_closed():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch.object(cmod, "_refreshed_actor", side_effect=ValueError("hostile db")):
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_refreshed_is_authenticated_fails_closed():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0

    class HostileRefreshed:
        @property
        def is_authenticated(self):
            raise KeyError("hostile is_auth")

    with patch.object(cmod, "_refreshed_actor", return_value=HostileRefreshed()):
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc_type",
    [pytest.param(TypeError, id="type-error"), pytest.param(ValueError, id="value-error")],
)
async def test_actor_is_current_hostile_scope_user_setitem_fails_closed(
    exc_type: type[Exception],
):
    """A raising ``scope['user'] =`` after refresh fails closed rather than escaping."""
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0

    class HostileDict(dict[str, object]):
        raise_enabled = False

        @override
        def __setitem__(self, k: str, v: object):
            if self.raise_enabled and k == "user":
                raise exc_type("hostile set user")
            super().__setitem__(k, v)

    hostile_scope = HostileDict(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    hostile_scope["user"] = scope["user"]
    hostile_scope.raise_enabled = True
    consumer.scope = hostile_scope
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_timestamp_write_still_succeeds():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 10.0

    class HostileDict(dict[str, object]):
        @override
        def __setitem__(self, k: str, v: object):
            if k == cmod._REVALIDATED_AT_SCOPE_KEY:
                raise ValueError("hostile timestamp")
            super().__setitem__(k, v)

    hostile_scope = HostileDict(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    # need user still there
    hostile_scope["user"] = scope["user"]
    consumer.scope = hostile_scope
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        with patch.object(cmod, "_monotonic", return_value=123.0):
            result = await cmod._actor_is_current(consumer)
            # timestamp write failing should not make it fail; still True
            assert result is True


@pytest.mark.asyncio
async def test_actor_is_current_hostile_consumer_scope_property_fails_closed():
    class HostileConsumer:
        @property
        def scope(self):
            raise AttributeError("hostile scope")

        revalidation_window = 0.0

    # basedpyright: the consumer whose scope read raises is the hostile input under test;
    # _actor_is_current types the parameter as _RevalidatedConsumer
    result = await cmod._actor_is_current(HostileConsumer())  # pyright: ignore[reportArgumentType]
    assert result is False


# ---------------------------------------------------------------------------
# revalidate_operation_actor - hostile handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revalidate_hostile_connection_acknowledged_fails_closed():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise AttributeError("hostile ack")

        websocket = Mock()
        view = Mock()

    result = await cmod.revalidate_operation_actor(HostileHandler())
    assert result is False


@pytest.mark.asyncio
async def test_revalidate_hostile_view_fails_closed():
    class Handler:
        connection_acknowledged = True

        @property
        def view(self):
            raise ValueError("hostile view")

        websocket = Mock()

    result = await cmod.revalidate_operation_actor(Handler())
    assert result is False


@pytest.mark.asyncio
async def test_revalidate_hostile_actor_lease_fails_closed():
    class HostileScope(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            raise TypeError("hostile lease get")

        @override
        def __setitem__(self, k: str, v: object):
            raise TypeError("hostile lease set")

    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = HostileScope()
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    # actor_lease will now raise ConfigurationError via connection_actor_state
    result = await cmod.revalidate_operation_actor(handler)
    assert result is False


@pytest.mark.asyncio
async def test_revalidate_revoked_short_circuits_without_db():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.view._revocation.decide()  # revoked
    handler.view.revalidation_window = 0.0
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    # Mock _revoke_connection to avoid real close
    with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mock_revoke:
        result = await cmod.revalidate_operation_actor(handler)
        assert result is False
        mock_revoke.assert_awaited_once()


# ---------------------------------------------------------------------------
# send_revalidated_operation_frame - hostile ws_consumer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_revalidated_hostile_ws_consumer_fails_closed():
    class HostileWS:
        @property
        def ws_consumer(self):
            raise KeyError("hostile ws_consumer")

    with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mock_revoke:
        # basedpyright: the socket whose ws_consumer read raises is the hostile input under test;
        # send_revalidated_operation_frame types the parameter as _GatedSocket
        await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # pyright: ignore[reportArgumentType]
        mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_revalidated_hostile_scope_fails_closed():
    class HostileScope(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            raise TypeError("hostile")

    consumer = Mock()
    consumer.scope = HostileScope()
    consumer._revocation = cmod._ConnectionRevocation()
    consumer.revalidation_window = 0.0
    ws = Mock()
    ws.ws_consumer = consumer
    with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mock_revoke:
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, AsyncMock())
        mock_revoke.assert_awaited_once()


# ---------------------------------------------------------------------------
# _RevocationGatedWebSocketAdapter.send_json - hostile message
# ---------------------------------------------------------------------------


class _RevalidatingAdapter(Protocol):
    """What the rows read off the generated adapter: its consumer and ``send_json``."""

    ws_consumer: RevalidatingGraphQLWSConsumer

    async def send_json(self, message: object) -> None: ...


def _build_consumer_and_adapter() -> tuple[
    RevalidatingGraphQLWSConsumer,
    _RevalidatingAdapter,
]:
    class FakeAdapter:
        async def send_json(self, message: object):
            pass

        async def close(self, code: int | None = None, reason: str | None = None):
            pass

    class FakeTransport:
        pass

    class FakeLegacy:
        pass

    class FakeBase:
        graphql_transport_ws_handler_class = FakeTransport
        graphql_ws_handler_class = FakeLegacy
        websocket_adapter_class = FakeAdapter

        def __init__(self, *a: object, **kw: object):
            pass

        async def disconnect(self, code: int):
            pass

    # basedpyright: a plain stand-in class carrying only the hooks the code under test reads;
    # build_revalidating_consumer_class types the parameter as type[GraphQLWSConsumer]
    cls = cmod.build_revalidating_consumer_class(FakeBase)  # pyright: ignore[reportArgumentType]
    consumer = cls.__new__(cls)
    # basedpyright: a stand-in scope dict; Channels types the consumer scope as its _ChannelScope
    # TypedDict
    consumer.scope = _fresh_scope()  # pyright: ignore[reportAttributeAccessIssue]
    consumer._revocation = cmod._ConnectionRevocation()
    consumer.revalidation_window = 0.0
    adapter_cls = cls.websocket_adapter_class
    # basedpyright: upstream types websocket_adapter_class a Callable factory, not a class
    adapter = adapter_cls.__new__(adapter_cls)  # pyright: ignore[reportCallIssue]
    adapter.ws_consumer = consumer
    return consumer, adapter


@pytest.mark.asyncio
async def test_send_json_hostile_message_get_fails_closed():
    consumer, adapter = _build_consumer_and_adapter()
    # Make the revalidation fail closed: mock _refreshed_actor to return None (revoked)
    with patch.object(cmod, "_refreshed_actor", return_value=None):
        # Also need to make scope have authenticated provenance so it actually tries DB
        adapter.ws_consumer.scope["user"] = Mock(is_authenticated=True)
        from django_strawberry_framework.utils.sessions import note_authenticated_actor

        # basedpyright: Channels types the consumer scope as its _ChannelScope TypedDict, while
        # note_authenticated_actor types the parameter as MutableMapping[str, object]
        note_authenticated_actor(adapter.ws_consumer.scope)  # pyright: ignore[reportArgumentType]

        class HostileMessage(dict[str, object]):
            @override
            def get(self, k: str, d: object = None):
                raise ValueError("hostile get")

        # Should not raise ValueError
        await adapter.send_json(HostileMessage({"type": "next"}))
        # After hostile, it should have revoked
        assert consumer._revocation.revoked is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message",
    [pytest.param(None, id="none"), pytest.param("not-a-dict", id="str")],
)
async def test_send_json_non_dict_message_does_not_escape(message: object):
    """A non-mapping frame is contained and revokes rather than raising."""
    consumer, adapter = _build_consumer_and_adapter()
    with patch.object(cmod, "_refreshed_actor", return_value=None):
        adapter.ws_consumer.scope["user"] = Mock(is_authenticated=True)
        from django_strawberry_framework.utils.sessions import note_authenticated_actor

        # basedpyright: Channels types the consumer scope as its _ChannelScope TypedDict, while
        # note_authenticated_actor types the parameter as MutableMapping[str, object]
        note_authenticated_actor(adapter.ws_consumer.scope)  # pyright: ignore[reportArgumentType]
        await adapter.send_json(message)
        assert consumer._revocation.revoked is True


@pytest.mark.asyncio
async def test_send_json_control_frame_hostile_scope_suppresses():
    _, adapter = _build_consumer_and_adapter()
    hostile_scope = _fresh_scope()
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=TypeError("hostile control scope"),
    ):
        # basedpyright: a stand-in scope dict; Channels types the consumer scope as its
        # _ChannelScope TypedDict
        adapter.ws_consumer.scope = hostile_scope  # pyright: ignore[reportAttributeAccessIssue]
        await adapter.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_send_json_control_frame_respects_revoked():
    consumer, adapter = _build_consumer_and_adapter()
    consumer._revocation.decide()
    # control frame should be suppressed when revoked
    with patch.object(
        adapter.__class__.__bases__[0],
        "send_json",
        new_callable=AsyncMock,
    ) as mock_super:
        await adapter.send_json({"type": "ping"})
        mock_super.assert_not_awaited()


# ---------------------------------------------------------------------------
# The fail-closed handlers' OWN failures: revoking is itself a suspending call
# on a hostile transport, so each nested revoke needs its own containment proof.
# A checkpoint whose denial path raises is a checkpoint that did not deny.
# ---------------------------------------------------------------------------


def _revalidating_consumer(scope: dict[str, object] | None = None):
    """A consumer duck-shape accepted by the module-level checkpoints."""
    consumer = Mock()
    consumer.scope = _fresh_scope() if scope is None else scope
    consumer._revocation = cmod._ConnectionRevocation()
    consumer.revalidation_window = 0.0
    return consumer


@pytest.mark.asyncio
async def test_send_revalidated_hostile_ws_consumer_with_failing_revoke_is_contained():
    """A hostile ``ws_consumer`` whose REVOKE also raises still does not escape."""

    class HostileWS:
        @property
        def ws_consumer(self):
            raise KeyError("hostile ws_consumer")

    with patch.object(
        cmod,
        "_revoke_connection",
        new_callable=AsyncMock,
        side_effect=ValueError("hostile close"),
    ) as mock_revoke:
        # basedpyright: the socket whose ws_consumer read raises is the hostile input under test;
        # send_revalidated_operation_frame types the parameter as _GatedSocket
        await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # pyright: ignore[reportArgumentType]
        mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_revalidated_cancellation_reading_revoked_is_re_raised():
    """``CancelledError`` reading the revocation flag propagates, not logged as a failure.

    These paths suspend, so a cancellation can genuinely arrive at them; recording
    one as a failed revalidation would misreport an ordinary shutdown.
    """

    class CancellingRevocation:
        @property
        def revoked(self):
            raise asyncio.CancelledError

    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()
    ws.ws_consumer._revocation = CancellingRevocation()

    with pytest.raises(asyncio.CancelledError):
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, AsyncMock())


@pytest.mark.asyncio
async def test_send_revalidated_cancellation_in_the_actor_check_is_re_raised():
    """``CancelledError`` from the actor check propagates rather than reading as denial."""
    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()

    with patch.object(
        cmod,
        "_actor_is_current",
        new_callable=AsyncMock,
        side_effect=asyncio.CancelledError,
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, AsyncMock())


@pytest.mark.asyncio
async def test_send_revalidated_stale_actor_with_failing_revoke_is_contained():
    """A stale actor whose revoke raises is contained; the frame is still suppressed.

    The stale-actor revoke is deliberately UNGUARDED, so its failure lands in the
    function's outer handler, which revokes again: two attempts, no escape. The
    retry is the point - one failed close must not leave the connection live.
    """
    send = AsyncMock()
    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()

    with (
        patch.object(cmod, "_actor_is_current", new_callable=AsyncMock, return_value=False),
        patch.object(
            cmod,
            "_revoke_connection",
            new_callable=AsyncMock,
            side_effect=ValueError("hostile close"),
        ) as mock_revoke,
    ):
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, send)

    assert mock_revoke.await_count == 2
    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_revalidated_failing_send_with_failing_revoke_is_contained():
    """A current actor whose SEND raises, and whose revoke then raises too, is contained.

    This is the one arm where the frame was authorized: the actor is current, so
    the failure is the transport's, and the revoke that answers it has its own
    guard rather than falling through to the outer handler.
    """
    send = AsyncMock(side_effect=ValueError("hostile transport"))
    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()

    with (
        patch.object(cmod, "_actor_is_current", new_callable=AsyncMock, return_value=True),
        patch.object(
            cmod,
            "_revoke_connection",
            new_callable=AsyncMock,
            side_effect=ValueError("hostile close"),
        ) as mock_revoke,
    ):
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, send)

    send.assert_awaited_once()
    mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_revalidated_cancellation_in_hostile_ws_consumer_revoke_is_re_raised():
    """A ``CancelledError`` from the hostile-``ws_consumer`` revoke propagates."""

    class HostileWS:
        @property
        def ws_consumer(self):
            raise KeyError("hostile ws_consumer")

    with patch.object(
        cmod,
        "_revoke_connection",
        new_callable=AsyncMock,
        side_effect=asyncio.CancelledError,
    ):
        with pytest.raises(asyncio.CancelledError):
            # basedpyright: the socket whose ws_consumer read raises is the hostile input under
            # test; send_revalidated_operation_frame types the parameter as _GatedSocket
            await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_send_revalidated_cancellation_in_authorized_frame_revoke_is_re_raised():
    """A ``CancelledError`` from the revoke after a failed authorized send propagates."""
    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()
    with (
        patch.object(cmod, "_actor_is_current", new_callable=AsyncMock, return_value=True),
        patch.object(
            cmod,
            "_revoke_connection",
            new_callable=AsyncMock,
            side_effect=asyncio.CancelledError,
        ),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(
                ws,
                {"type": "next"},
                AsyncMock(side_effect=ValueError("hostile transport")),
            )


@pytest.mark.asyncio
async def test_send_revalidated_cancellation_in_outer_lease_revoke_is_re_raised():
    """A ``CancelledError`` from the outer-arm revoke (hostile lease) propagates."""
    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()
    with (
        patch.object(cmod, "actor_lease", side_effect=TypeError("hostile lease")),
        patch.object(
            cmod,
            "_revoke_connection",
            new_callable=AsyncMock,
            side_effect=asyncio.CancelledError,
        ),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, AsyncMock())


@pytest.mark.asyncio
async def test_send_revalidated_outer_failure_with_failing_revoke_is_contained():
    """A hostile lease AND a failing revoke together still do not escape."""
    send = AsyncMock()
    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()

    with (
        patch.object(cmod, "actor_lease", side_effect=TypeError("hostile lease")),
        patch.object(
            cmod,
            "_revoke_connection",
            new_callable=AsyncMock,
            side_effect=ValueError("hostile close"),
        ) as mock_revoke,
    ):
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, send)

    mock_revoke.assert_awaited_once()
    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_actor_is_current_hostile_is_authenticated_and_hostile_provenance_denies():
    """When BOTH the actor read and the provenance check fail, the answer is denial."""

    class HostileIsAuth:
        @property
        def is_authenticated(self):
            raise ValueError("hostile is_authenticated")

    consumer = _revalidating_consumer()
    consumer.scope["user"] = HostileIsAuth()

    with patch.object(
        cmod,
        "connection_was_authenticated",
        side_effect=KeyError("hostile provenance"),
    ):
        assert await cmod._actor_is_current(consumer) is False


@pytest.mark.asyncio
async def test_actor_is_current_cancellation_in_the_provenance_check_is_re_raised():
    """``CancelledError`` from the provenance fallback propagates."""

    class HostileIsAuth:
        @property
        def is_authenticated(self):
            raise ValueError("hostile is_authenticated")

    consumer = _revalidating_consumer()
    consumer.scope["user"] = HostileIsAuth()

    with patch.object(
        cmod,
        "connection_was_authenticated",
        side_effect=asyncio.CancelledError,
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_send_json_cancellation_reading_the_message_type_is_re_raised():
    """``CancelledError`` from the frame's own ``get`` propagates out of the adapter."""
    _, adapter = _build_consumer_and_adapter()

    class CancellingMessage(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await adapter.send_json(CancellingMessage({"type": "next"}))


@pytest.mark.asyncio
async def test_send_json_hostile_message_with_failing_delegate_is_contained():
    """An unreadable frame whose fail-closed delegate ALSO raises does not escape."""
    _, adapter = _build_consumer_and_adapter()

    class HostileMessage(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            raise ValueError("hostile get")

    with patch.object(
        cmod,
        "send_revalidated_operation_frame",
        new_callable=AsyncMock,
        side_effect=ValueError("hostile delegate"),
    ) as mock_send:
        await adapter.send_json(HostileMessage({"type": "next"}))
        mock_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_json_control_frame_unreadable_revoked_flag_suppresses_the_frame():
    """A control frame reads an unreadable revocation flag as REVOKED and sends nothing."""
    _, adapter = _build_consumer_and_adapter()

    class HostileRevocation:
        @property
        def revoked(self):
            raise ValueError("hostile revoked")

    # basedpyright: the hostile revocation is the input under test, and it is not a
    # _ConnectionRevocation
    adapter.ws_consumer._revocation = HostileRevocation()  # pyright: ignore[reportAttributeAccessIssue]

    with patch.object(
        adapter.__class__.__bases__[0],
        "send_json",
        new_callable=AsyncMock,
    ) as mock_super:
        await adapter.send_json({"type": "ping"})
        mock_super.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_json_control_frame_cancellation_reading_revoked_is_re_raised():
    """``CancelledError`` reading the flag for a control frame propagates."""
    _, adapter = _build_consumer_and_adapter()

    class CancellingRevocation:
        @property
        def revoked(self):
            raise asyncio.CancelledError

    # basedpyright: the cancelling revocation is the input under test, and it is not a
    # _ConnectionRevocation
    adapter.ws_consumer._revocation = CancellingRevocation()  # pyright: ignore[reportAttributeAccessIssue]

    with pytest.raises(asyncio.CancelledError):
        await adapter.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_send_json_information_frame_with_failing_delegate_is_contained():
    """A failing outbound checkpoint on an information-bearing frame does not escape."""
    _, adapter = _build_consumer_and_adapter()

    with patch.object(
        cmod,
        "send_revalidated_operation_frame",
        new_callable=AsyncMock,
        side_effect=ValueError("hostile delegate"),
    ) as mock_send:
        await adapter.send_json({"type": "next"})
        mock_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_json_information_frame_cancellation_is_re_raised():
    """``CancelledError`` from the outbound checkpoint propagates."""
    _, adapter = _build_consumer_and_adapter()

    with patch.object(
        cmod,
        "send_revalidated_operation_frame",
        new_callable=AsyncMock,
        side_effect=asyncio.CancelledError,
    ):
        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json({"type": "next"})


# ---------------------------------------------------------------------------
# _revoke_connection - hostile websocket
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revoke_connection_hostile_ws_consumer_does_not_raise():
    class HostileWS:
        @property
        def ws_consumer(self):
            raise AttributeError("hostile ws_consumer")

    # Should not raise
    # basedpyright: the socket whose ws_consumer read raises is the hostile input under test;
    # _revoke_connection types the parameter as _GatedSocket
    await cmod._revoke_connection(HostileWS())  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_revoke_connection_hostile_revocation_decide_does_not_raise():
    class HostileRevocation:
        def decide(self):
            raise ValueError("hostile decide")

        @property
        def attempts(self):
            return 0

    ws = Mock()
    ws.ws_consumer = Mock(_revocation=HostileRevocation())
    await cmod._revoke_connection(ws)
    # No raise


# ---------------------------------------------------------------------------
# resolved_revalidation_window - construction-time domain
# ---------------------------------------------------------------------------


class _WindowIntSubclass(int):
    """An ``int`` subclass the exact-type window gate must reject."""


class _WindowFloatSubclass(float):
    """A ``float`` subclass the exact-type window gate must reject."""


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(True, id="true"),
        pytest.param(False, id="false"),
        pytest.param(_WindowIntSubclass(1), id="int-subclass"),
        pytest.param(_WindowFloatSubclass(1.0), id="float-subclass"),
        pytest.param("1.0", id="string"),
        pytest.param(None, id="none"),
        pytest.param([], id="list"),
        pytest.param({}, id="dict"),
    ],
)
def test_resolved_window_rejects_bool_and_subclasses(bad: object):
    """Only the built-in ``int`` and ``float`` types are a usable window."""
    with pytest.raises(ConfigurationError):
        cmod.resolved_revalidation_window(bad)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="inf"),
        pytest.param(float("-inf"), id="neg-inf"),
        pytest.param(-0.1, id="negative-float"),
        pytest.param(-1, id="negative-int"),
    ],
)
def test_resolved_window_rejects_nan_and_inf_and_negative(bad: float):
    """A non-finite or negative number is not a usable number of seconds."""
    with pytest.raises(ConfigurationError):
        cmod.resolved_revalidation_window(bad)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(0, 0.0, id="int-zero"),
        pytest.param(0.0, 0.0, id="float-zero"),
        pytest.param(1, 1.0, id="int-one"),
        pytest.param(1.5, 1.5, id="float-fraction"),
        pytest.param(10**300, float(10**300), id="astronomical-int"),
    ],
)
def test_resolved_window_accepts_zero_and_positive(value: float, expected: float):
    """Zero and every finite non-negative number coerce to ``float``."""
    assert cmod.resolved_revalidation_window(value) == expected


def test_resolved_window_huge_int_overflow_is_configuration_error():
    """An ``int`` with no ``float`` image is a typed construction error, chained."""
    huge = 10**10000
    with pytest.raises(ConfigurationError) as excinfo:
        cmod.resolved_revalidation_window(huge)
    assert isinstance(excinfo.value.__cause__, OverflowError)


# ---------------------------------------------------------------------------
# _host_validation_request - WebSocket handshake Host projection
# ---------------------------------------------------------------------------


def test_host_validation_absent_headers_and_server_uses_defaults():
    """A scope with neither Host headers nor ``server`` reconstructs Django's literals."""
    scope: dict[str, object] = {}
    # basedpyright: the absent keys (no headers, no server) are the input under test; asgiref's
    # WebSocketScope declares every key required
    req = cmod._host_validation_request(scope)  # pyright: ignore[reportArgumentType]
    assert req.META["SERVER_NAME"] == "unknown"
    assert req.META["SERVER_PORT"] == "0"
    assert "HTTP_HOST" not in req.META


def test_host_validation_duplicate_hosts_are_comma_joined():
    """Two Host headers become Django's comma-joined form, not a silently picked one."""
    scope = websocket_scope([(b"host", b"a.com"), (b"host", b"b.com")], ("x", 80))
    req = cmod._host_validation_request(scope)
    assert req.META["HTTP_HOST"] == "a.com,b.com"


def test_host_validation_case_insensitive_header():
    """Header names are normalized; an odd-cased ``Host`` still projects."""
    scope = websocket_scope([(b"Host", b"example.com")], ("x", 80))
    req = cmod._host_validation_request(scope)
    assert req.META["HTTP_HOST"] == "example.com"


@pytest.mark.parametrize(
    "server",
    [
        pytest.param(None, id="none"),
        pytest.param(0, id="zero"),
        pytest.param(False, id="false"),
        pytest.param("", id="empty-str"),
    ],
)
def test_host_validation_server_absent_vs_null(server: object):
    """A falsy ``scope['server']`` uses the same ``unknown`` reconstruction as absence."""
    scope = {"headers": [], "server": server}
    # basedpyright: the ill-typed server value is the input under test; asgiref's WebSocketScope
    # types server as tuple[str, int | None] | None
    req = cmod._host_validation_request(scope)  # pyright: ignore[reportArgumentType]
    assert req.META["SERVER_NAME"] == "unknown"


# ---------------------------------------------------------------------------
# CancelledError propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revalidate_hostile_ack_cancelled_propagates():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise asyncio.CancelledError("hostile cancelled")

        websocket = Mock()
        view = Mock()

    with pytest.raises(asyncio.CancelledError):
        await cmod.revalidate_operation_actor(HostileHandler())


@pytest.mark.asyncio
async def test_revalidate_hostile_ack_websocket_cancelled_propagates():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        @property
        def websocket(self):
            raise asyncio.CancelledError("hostile websocket cancelled")

        view = Mock()

    with pytest.raises(asyncio.CancelledError):
        await cmod.revalidate_operation_actor(HostileHandler())


@pytest.mark.asyncio
async def test_revalidate_hostile_view_cancelled_propagates():
    class Handler:
        connection_acknowledged = True

        @property
        def view(self):
            raise asyncio.CancelledError("hostile view cancelled")

        websocket = Mock()

    with pytest.raises(asyncio.CancelledError):
        await cmod.revalidate_operation_actor(Handler())


@pytest.mark.asyncio
async def test_revalidate_hostile_revoked_cancelled_propagates():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    # Make _revocation.revoked raise Cancelled
    type(handler.view._revocation).revoked = property(
        lambda self: (_ for _ in ()).throw(asyncio.CancelledError("cancelled")),
    )
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with pytest.raises(asyncio.CancelledError):
        await cmod.revalidate_operation_actor(handler)


@pytest.mark.asyncio
async def test_revalidate_hostile_is_current_cancelled_propagates():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    handler.view.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(handler.view.scope)
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.view.revalidation_window = 0.0
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch.object(cmod, "_actor_is_current", side_effect=asyncio.CancelledError("cancelled")):
        with pytest.raises(asyncio.CancelledError):
            await cmod.revalidate_operation_actor(handler)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_scope_get_propagates():
    class HostileConsumer:
        @property
        def scope(self):
            raise asyncio.CancelledError("cancelled scope")

        revalidation_window = 0.0

    with pytest.raises(asyncio.CancelledError):
        # basedpyright: the consumer whose scope read raises is the hostile input under test;
        # _actor_is_current types the parameter as _RevalidatedConsumer
        await cmod._actor_is_current(HostileConsumer())  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_actor_get_propagates():
    class HostileScope(dict[str, object]):
        @override
        def get(self, k: str, d: object = None):
            if k == "user":
                raise asyncio.CancelledError("cancelled get")
            return super().get(k, d)

    scope = HostileScope()
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_is_authenticated_propagates():
    class HostileUser:
        @property
        def is_authenticated(self):
            raise asyncio.CancelledError("cancelled is_auth")

    scope: dict[str, object] = {"user": HostileUser()}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_note_propagates():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch(
        "django_strawberry_framework.consumers.note_authenticated_actor",
        side_effect=asyncio.CancelledError("cancelled note"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_window_propagates():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope

    class HostileConsumer:
        @property
        def revalidation_window(self):
            raise asyncio.CancelledError("cancelled window")

        @property
        def scope(self):
            return scope

    with pytest.raises(asyncio.CancelledError):
        # basedpyright: the consumer whose revalidation_window read raises is the hostile input
        # under test; _actor_is_current types the parameter as _RevalidatedConsumer
        await cmod._actor_is_current(HostileConsumer())  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_cache_comparison_propagates():
    class HostileFloat:
        def __gt__(self, other: object):
            raise asyncio.CancelledError("cancelled gt")

    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    actor_state = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY] = actor_state
    actor_state.authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = HostileFloat()
    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_refreshed_propagates():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch.object(cmod, "_refreshed_actor", side_effect=asyncio.CancelledError("cancelled")):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_refreshed_is_auth_propagates():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0

    class HostileRefreshed:
        @property
        def is_authenticated(self):
            raise asyncio.CancelledError("cancelled")

    with patch.object(cmod, "_refreshed_actor", return_value=HostileRefreshed()):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_scope_user_set_propagates():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0

    class HostileScope(dict[str, object]):
        raise_enabled = False

        @override
        def __setitem__(self, k: str, v: object):
            if self.raise_enabled and k == "user":
                raise asyncio.CancelledError("cancelled set user")
            super().__setitem__(k, v)

    hostile_scope = HostileScope(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    hostile_scope["user"] = scope["user"]
    hostile_scope.raise_enabled = True
    consumer.scope = hostile_scope
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_timestamp_set_propagates():
    scope: dict[str, object] = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 10.0

    class HostileScope(dict[str, object]):
        raise_enabled = False

        @override
        def __setitem__(self, k: str, v: object):
            if self.raise_enabled and k == cmod._REVALIDATED_AT_SCOPE_KEY:
                raise asyncio.CancelledError("cancelled timestamp")
            super().__setitem__(k, v)

    hostile_scope = HostileScope(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    hostile_scope["user"] = scope["user"]
    hostile_scope.raise_enabled = True
    consumer.scope = hostile_scope
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        with patch.object(cmod, "_monotonic", return_value=1.0):
            with pytest.raises(asyncio.CancelledError):
                await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_send_revalidated_hostile_ws_consumer_cancelled_propagates():
    class HostileWS:
        @property
        def ws_consumer(self):
            raise asyncio.CancelledError("cancelled ws_consumer")

    with pytest.raises(asyncio.CancelledError):
        # basedpyright: the socket whose ws_consumer read raises is the hostile input under test;
        # send_revalidated_operation_frame types the parameter as _GatedSocket
        await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_send_revalidated_hostile_scope_cancelled_propagates():
    consumer = Mock()
    consumer.scope = _fresh_scope()
    # Make actor_lease raise Cancelled
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=asyncio.CancelledError("cancelled lease"),
    ):
        ws = Mock()
        ws.ws_consumer = consumer
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, AsyncMock())


@pytest.mark.asyncio
async def test_send_json_hostile_message_cancelled_propagates():
    _, adapter = _build_consumer_and_adapter()
    with patch.object(
        cmod,
        "send_revalidated_operation_frame",
        side_effect=asyncio.CancelledError("cancelled"),
    ):

        class HostileMessage(dict[str, object]):
            @override
            def get(self, k: str, d: object = None):
                raise ValueError("hostile")

        # ValueError triggers the except that calls send_revalidated, which now raises Cancelled
        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json(HostileMessage({"type": "next"}))


@pytest.mark.asyncio
async def test_send_json_control_cancelled_propagates():
    _, adapter = _build_consumer_and_adapter()
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=asyncio.CancelledError("cancelled lease"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_revoke_connection_hostile_ws_consumer_cancelled_propagates():
    class HostileWS:
        @property
        def ws_consumer(self):
            raise asyncio.CancelledError("cancelled")

    with pytest.raises(asyncio.CancelledError):
        # basedpyright: the socket whose ws_consumer read raises is the hostile input under test;
        # _revoke_connection types the parameter as _GatedSocket
        await cmod._revoke_connection(HostileWS())  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_revoke_connection_hostile_decide_cancelled_propagates():
    class HostileRevocation:
        def decide(self):
            raise asyncio.CancelledError("cancelled decide")

        @property
        def attempts(self):
            return 0

    ws = Mock()
    ws.ws_consumer = Mock(_revocation=HostileRevocation())
    with pytest.raises(asyncio.CancelledError):
        await cmod._revoke_connection(ws)


# ---------------------------------------------------------------------------
# Nested fail-closed arms (ack / revoked / lease / outbound send)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revalidate_ack_hostile_websocket_value_error_fails_closed():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        @property
        def websocket(self):
            raise ValueError("hostile websocket")

        view = Mock()

    result = await cmod.revalidate_operation_actor(HostileHandler())
    assert result is False


@pytest.mark.asyncio
async def test_revalidate_ack_hostile_revoke_value_error_still_fails_closed():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        websocket = Mock()
        view = Mock()

    with patch.object(cmod, "_revoke_connection", side_effect=ValueError("hostile revoke")):
        result = await cmod.revalidate_operation_actor(HostileHandler())
        assert result is False


@pytest.mark.asyncio
async def test_revalidate_revoked_hostile_fails_closed():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    # Make revoked raise ValueError
    type(handler.view._revocation).revoked = property(
        lambda self: (_ for _ in ()).throw(ValueError("hostile revoked")),
    )
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock):
        result = await cmod.revalidate_operation_actor(handler)
        assert result is False
    # Restore
    type(handler.view._revocation).revoked = property(
        lambda self: self.state != cmod._REVOCATION_PERMITTED,
    )


@pytest.mark.asyncio
async def test_revalidate_is_current_hostile_fails_closed():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    handler.view.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(handler.view.scope)
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.view.revalidation_window = 0.0
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch.object(cmod, "_actor_is_current", side_effect=ValueError("hostile is_current")):
        with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mock_revoke:
            result = await cmod.revalidate_operation_actor(handler)
            assert result is False
            mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_revalidate_actor_lease_hostile_value_error_fails_closed():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.view.revalidation_window = 0.0
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=ValueError("hostile lease"),
    ):
        with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mock_revoke:
            result = await cmod.revalidate_operation_actor(handler)
            assert result is False
            mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_actor_is_current_connection_was_authenticated_hostile():
    scope: dict[str, object] = {"user": None}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch(
        "django_strawberry_framework.consumers.connection_was_authenticated",
        side_effect=ValueError("hostile"),
    ):
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
async def test_send_revalidated_revoked_hostile():
    consumer = Mock()
    consumer.scope = _fresh_scope()
    # Make revoked raise
    type(consumer._revocation).revoked = property(
        lambda self: (_ for _ in ()).throw(ValueError("hostile")),
    )
    # Need to actually set _revocation to a real one with hostile property
    # Use a mock revocation
    mock_rev = Mock()
    type(mock_rev).revoked = property(lambda self: (_ for _ in ()).throw(ValueError("hostile")))
    consumer._revocation = mock_rev
    consumer.revalidation_window = 0.0
    ws = Mock()
    ws.ws_consumer = consumer
    with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mock_revoke:
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, AsyncMock())
        mock_revoke.assert_awaited_once()
    # Restore
    consumer._revocation = cmod._ConnectionRevocation()


@pytest.mark.asyncio
async def test_send_revalidated_is_current_hostile():
    consumer = Mock()
    consumer.scope = _fresh_scope()
    consumer.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(consumer.scope)
    consumer._revocation = cmod._ConnectionRevocation()
    consumer.revalidation_window = 0.0
    ws = Mock()
    ws.ws_consumer = consumer
    with patch.object(cmod, "_actor_is_current", side_effect=ValueError("hostile")):
        with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mock_revoke:
            await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, AsyncMock())
            mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_revalidated_send_hostile():
    consumer = Mock()
    consumer.scope = _fresh_scope()
    consumer.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(consumer.scope)
    consumer._revocation = cmod._ConnectionRevocation()
    consumer.revalidation_window = 0.0
    ws = Mock()
    ws.ws_consumer = consumer

    async def hostile_send(msg: object):
        raise ValueError("hostile send")

    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, hostile_send)
        # Should have revoked, not raised
        assert consumer._revocation.revoked is True


@pytest.mark.asyncio
async def test_send_json_control_hostile_send_suppresses():
    _, adapter = _build_consumer_and_adapter()
    with patch.object(
        adapter.__class__.__bases__[0],
        "send_json",
        side_effect=ValueError("hostile super"),
    ):
        # Control frame should be suppressed on hostile super, not propagate
        await adapter.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_revalidate_ack_hostile_revoke_cancelled():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        websocket = Mock()
        view = Mock()

    with patch.object(
        cmod,
        "_revoke_connection",
        side_effect=asyncio.CancelledError("cancelled revoke"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.revalidate_operation_actor(HostileHandler())


@pytest.mark.asyncio
async def test_revalidate_outer_lease_cancelled():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.view.revalidation_window = 0.0
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=asyncio.CancelledError("cancelled lease"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.revalidate_operation_actor(handler)


@pytest.mark.asyncio
async def test_revalidate_outer_lease_hostile_revoke_cancelled():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.view.revalidation_window = 0.0
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=ValueError("hostile lease"),
    ):
        with patch.object(
            cmod,
            "_revoke_connection",
            side_effect=asyncio.CancelledError("cancelled"),
        ):
            with pytest.raises(asyncio.CancelledError):
                await cmod.revalidate_operation_actor(handler)


@pytest.mark.asyncio
async def test_send_revalidated_send_cancelled():
    consumer = Mock()
    consumer.scope = _fresh_scope()
    consumer.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(consumer.scope)
    consumer._revocation = cmod._ConnectionRevocation()
    consumer.revalidation_window = 0.0
    ws = Mock()
    ws.ws_consumer = consumer

    async def hostile_send(msg: object):
        raise asyncio.CancelledError("cancelled send")

    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, hostile_send)


@pytest.mark.asyncio
async def test_send_json_control_send_cancelled():
    _, adapter = _build_consumer_and_adapter()
    with patch.object(
        adapter.__class__.__bases__[0],
        "send_json",
        side_effect=asyncio.CancelledError("cancelled"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json({"type": "ping"})


def test_utils_connection_actor_state_hostile_isinstance():
    """A raising ``isinstance`` on a stored actor state is a typed configuration error."""
    scope = {_ACTOR_STATE_SCOPE_KEY: object()}
    with patch(
        "django_strawberry_framework.utils.sessions.isinstance",
        side_effect=ValueError("hostile"),
    ):
        with pytest.raises(ConfigurationError):
            connection_actor_state(scope)


@pytest.mark.asyncio
async def test_revalidate_outer_lease_value_error_revoke_value_error():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    handler.view._revocation = cmod._ConnectionRevocation()
    handler.view.revalidation_window = 0.0
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=ValueError("hostile"),
    ):
        with patch.object(cmod, "_revoke_connection", side_effect=ValueError("hostile revoke")):
            result = await cmod.revalidate_operation_actor(handler)
            assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_connection_was_authenticated_cancelled():
    scope: dict[str, object] = {"user": None}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch(
        "django_strawberry_framework.consumers.connection_was_authenticated",
        side_effect=asyncio.CancelledError("cancelled"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)
