"""Hostile-input containment for the WebSocket consumer (spec-046).

Covers the five axes at the strongest tier per AGENTS.md (package tests via
WebsocketCommunicator when the WebSocket path is reachable, otherwise direct
unit calls). Every hostile arm must not escape as TypeError/ValueError/
AttributeError/IndexError/KeyError; revalidation fails closed (revoked) and
config fails as ConfigurationError.

Lines pinned: the new except/log/return arms added for hostile scope/actor/
window/message/hostile handler.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from django_strawberry_framework import consumers as cmod
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.sessions import (
    _ACTOR_STATE_SCOPE_KEY,
    ConnectionActorState,
    connection_actor_state,
)


def _fresh_scope():
    scope: dict = {}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    return scope


# ---------------------------------------------------------------------------
# utils/sessions - hostile scope containment (owning layer)
# ---------------------------------------------------------------------------


def test_connection_actor_state_hostile_get_raises_configuration_error():
    class HostileScope(dict):
        def get(self, k, d=None):
            raise TypeError("hostile get")

    with pytest.raises(ConfigurationError) as excinfo:
        connection_actor_state(HostileScope())  # type: ignore[arg-type]
    assert excinfo.value.__cause__ is not None
    assert isinstance(excinfo.value.__cause__, TypeError)


def test_connection_actor_state_hostile_setitem_raises_configuration_error():
    class HostileScope(dict):
        def __setitem__(self, k, v):
            raise ValueError("hostile set")

    with pytest.raises(ConfigurationError) as excinfo:
        connection_actor_state(HostileScope())  # type: ignore[arg-type]
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_connection_actor_state_corrupted_value_raises_configuration_error():
    scope = {_ACTOR_STATE_SCOPE_KEY: "not-a-state"}
    with pytest.raises(ConfigurationError, match="corrupted"):
        connection_actor_state(scope)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# consumers._actor_is_current - hostile containment (fail-closed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_actor_is_current_hostile_scope_get_fails_closed():
    class HostileScope(dict):
        def get(self, k, d=None):
            if k == "user":
                raise TypeError("hostile get user")
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

    scope = {"user": HostileUser()}
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

    scope = {"user": HostileUser()}
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
    class HostileScope(dict):
        def get(self, k, d=None):
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
    scope2 = {"user": Mock(is_authenticated=True)}
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
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    # hostile property for revalidation_window
    type(consumer).revalidation_window = property(
        lambda self: (_ for _ in ()).throw(AttributeError("hostile window")),
    )  # type: ignore[attr-defined]

    # Actually Mock property trick is messy; use a real object with hostile property
    class HostileConsumer:
        @property
        def revalidation_window(self):
            raise AttributeError("hostile window")

        @property
        def scope(self):
            return scope

    hc = HostileConsumer()
    result = await cmod._actor_is_current(hc)  # type: ignore[arg-type]
    assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_window_comparison_falls_through_to_db():
    class HostileFloat:
        def __gt__(self, other):
            raise AttributeError("hostile gt")

    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY].authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = HostileFloat()  # type: ignore[assignment]
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
    class HostileScope(dict):
        def get(self, k, d=None):
            if k == cmod._REVALIDATED_AT_SCOPE_KEY:
                raise IndexError("hostile revalidated get")
            if k == "user":
                return Mock(is_authenticated=True)
            return super().get(k, d)

    scope = HostileScope()
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY].authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 10.0
    with patch.object(cmod, "_refreshed_actor", new_callable=AsyncMock) as mock_ref:
        mock_ref.return_value = Mock(is_authenticated=True)
        result = await cmod._actor_is_current(consumer)
        assert result is True


@pytest.mark.asyncio
async def test_actor_is_current_hostile_refreshed_actor_fails_closed():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch.object(cmod, "_refreshed_actor", side_effect=ValueError("hostile db")):
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_refreshed_is_authenticated_fails_closed():
    scope = {"user": Mock(is_authenticated=True)}
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
async def test_actor_is_current_hostile_scope_user_setitem_fails_closed():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0

    class HostileDict(dict):
        def __setitem__(self, k, v):
            if k == "user":
                raise TypeError("hostile set user")
            super().__setitem__(k, v)

    hostile_scope = HostileDict(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    consumer.scope = hostile_scope
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_hostile_timestamp_write_still_succeeds():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 10.0

    class HostileDict(dict):
        def __setitem__(self, k, v):
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

    result = await cmod._actor_is_current(HostileConsumer())  # type: ignore[arg-type]
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

    result = await cmod.revalidate_operation_actor(HostileHandler())  # type: ignore[arg-type]
    assert result is False


@pytest.mark.asyncio
async def test_revalidate_hostile_view_fails_closed():
    class Handler:
        connection_acknowledged = True

        @property
        def view(self):
            raise ValueError("hostile view")

        websocket = Mock()

    result = await cmod.revalidate_operation_actor(Handler())  # type: ignore[arg-type]
    assert result is False


@pytest.mark.asyncio
async def test_revalidate_hostile_actor_lease_fails_closed():
    class HostileScope(dict):
        def get(self, k, d=None):
            raise TypeError("hostile lease get")

        def __setitem__(self, k, v):
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
        await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # type: ignore[arg-type]
        mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_revalidated_hostile_scope_fails_closed():
    class HostileScope(dict):
        def get(self, k, d=None):
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


def _build_consumer_and_adapter():
    class FakeAdapter:
        async def send_json(self, message):
            pass

        async def close(self, code=None, reason=None):
            pass

    class FakeTransport:
        pass

    class FakeLegacy:
        pass

    class FakeBase:
        graphql_transport_ws_handler_class = FakeTransport
        graphql_ws_handler_class = FakeLegacy
        websocket_adapter_class = FakeAdapter

        def __init__(self, *a, **kw):
            pass

        async def disconnect(self, code):
            pass

    cls = cmod.build_revalidating_consumer_class(FakeBase)
    consumer = cls.__new__(cls)
    consumer.scope = _fresh_scope()
    consumer._revocation = cmod._ConnectionRevocation()
    consumer.revalidation_window = 0.0
    adapter_cls = cls.websocket_adapter_class
    adapter = adapter_cls.__new__(adapter_cls)
    adapter.ws_consumer = consumer  # type: ignore[attr-defined]
    return consumer, adapter


@pytest.mark.asyncio
async def test_send_json_hostile_message_get_fails_closed():
    _, adapter = _build_consumer_and_adapter()
    # Make the revalidation fail closed: mock _refreshed_actor to return None (revoked)
    with patch.object(cmod, "_refreshed_actor", return_value=None):
        # Also need to make scope have authenticated provenance so it actually tries DB
        adapter.ws_consumer.scope["user"] = Mock(is_authenticated=True)
        from django_strawberry_framework.utils.sessions import note_authenticated_actor

        note_authenticated_actor(adapter.ws_consumer.scope)

        class HostileMessage(dict):
            def get(self, k, d=None):
                raise ValueError("hostile get")

        # Should not raise ValueError
        await adapter.send_json(HostileMessage({"type": "next"}))  # type: ignore[arg-type]
        # After hostile, it should have revoked
        assert adapter.ws_consumer._revocation.revoked is True


@pytest.mark.asyncio
async def test_send_json_hostile_message_none_and_str_do_not_escape():
    _, adapter = _build_consumer_and_adapter()
    with patch.object(cmod, "_refreshed_actor", return_value=None):
        adapter.ws_consumer.scope["user"] = Mock(is_authenticated=True)
        from django_strawberry_framework.utils.sessions import note_authenticated_actor

        note_authenticated_actor(adapter.ws_consumer.scope)
        await adapter.send_json(None)  # type: ignore[arg-type]
        assert adapter.ws_consumer._revocation.revoked is True
    # Reset for second
    _, adapter2 = _build_consumer_and_adapter()
    with patch.object(cmod, "_refreshed_actor", return_value=None):
        adapter2.ws_consumer.scope["user"] = Mock(is_authenticated=True)
        from django_strawberry_framework.utils.sessions import note_authenticated_actor

        note_authenticated_actor(adapter2.ws_consumer.scope)
        await adapter2.send_json("not-a-dict")  # type: ignore[arg-type]
        assert adapter2.ws_consumer._revocation.revoked is True


@pytest.mark.asyncio
async def test_send_json_control_frame_hostile_scope_suppresses():
    _, adapter = _build_consumer_and_adapter()
    hostile_scope = _fresh_scope()
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=TypeError("hostile control scope"),
    ):
        adapter.ws_consumer.scope = hostile_scope  # type: ignore[assignment]
        await adapter.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_send_json_control_frame_respects_revoked():
    _, adapter = _build_consumer_and_adapter()
    adapter.ws_consumer._revocation.decide()
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


def _revalidating_consumer(scope=None):
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
        await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # type: ignore[arg-type]
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
async def test_send_revalidated_cancellation_in_each_nested_revoke_is_re_raised():
    """A ``CancelledError`` from a NESTED revoke propagates from all three of its sites.

    The nested revokes swallow ordinary failures so a hostile transport cannot
    keep the connection alive; a cancellation is the one thing they must not
    swallow, because it means the surrounding task is being torn down and there
    is nothing left to fail closed for.
    """

    class HostileWS:
        @property
        def ws_consumer(self):
            raise KeyError("hostile ws_consumer")

    cancelling_revoke = {"new_callable": AsyncMock, "side_effect": asyncio.CancelledError}

    # 1. The hostile-``ws_consumer`` arm.
    with patch.object(cmod, "_revoke_connection", **cancelling_revoke):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # type: ignore[arg-type]

    # 2. The authorized-frame arm, where ``send`` itself failed first.
    ws = Mock()
    ws.ws_consumer = _revalidating_consumer()
    with (
        patch.object(cmod, "_actor_is_current", new_callable=AsyncMock, return_value=True),
        patch.object(cmod, "_revoke_connection", **cancelling_revoke),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(
                ws,
                {"type": "next"},
                AsyncMock(side_effect=ValueError("hostile transport")),
            )

    # 3. The outer arm, reached when the lease itself is hostile.
    ws2 = Mock()
    ws2.ws_consumer = _revalidating_consumer()
    with (
        patch.object(cmod, "actor_lease", side_effect=TypeError("hostile lease")),
        patch.object(cmod, "_revoke_connection", **cancelling_revoke),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(ws2, {"type": "next"}, AsyncMock())


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

    class CancellingMessage(dict):
        def get(self, k, d=None):
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await adapter.send_json(CancellingMessage({"type": "next"}))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_send_json_hostile_message_with_failing_delegate_is_contained():
    """An unreadable frame whose fail-closed delegate ALSO raises does not escape."""
    _, adapter = _build_consumer_and_adapter()

    class HostileMessage(dict):
        def get(self, k, d=None):
            raise ValueError("hostile get")

    with patch.object(
        cmod,
        "send_revalidated_operation_frame",
        new_callable=AsyncMock,
        side_effect=ValueError("hostile delegate"),
    ) as mock_send:
        await adapter.send_json(HostileMessage({"type": "next"}))  # type: ignore[arg-type]
        mock_send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_json_control_frame_unreadable_revoked_flag_suppresses_the_frame():
    """A control frame reads an unreadable revocation flag as REVOKED and sends nothing."""
    _, adapter = _build_consumer_and_adapter()

    class HostileRevocation:
        @property
        def revoked(self):
            raise ValueError("hostile revoked")

    adapter.ws_consumer._revocation = HostileRevocation()  # type: ignore[attr-defined]

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

    adapter.ws_consumer._revocation = CancellingRevocation()  # type: ignore[attr-defined]

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
    await cmod._revoke_connection(HostileWS())  # type: ignore[arg-type]


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
# resolved_revalidation_window - shape/lexical (already covered but pinned)
# ---------------------------------------------------------------------------


def test_resolved_window_rejects_bool_and_subclasses():
    class MyInt(int):
        pass

    class MyFloat(float):
        pass

    for bad in [
        True,
        False,
        MyInt(1),
        MyFloat(1.0),
        "1.0",
        None,
        [],
        {},
    ]:
        with pytest.raises(ConfigurationError):
            cmod.resolved_revalidation_window(bad)  # type: ignore[arg-type]


def test_resolved_window_rejects_nan_and_inf_and_negative():
    for bad in [
        float("nan"),
        float("inf"),
        float("-inf"),
        -0.1,
        -1,
    ]:
        with pytest.raises(ConfigurationError):
            cmod.resolved_revalidation_window(bad)


def test_resolved_window_accepts_zero_and_positive():
    assert cmod.resolved_revalidation_window(0) == 0.0
    assert cmod.resolved_revalidation_window(0.0) == 0.0
    assert cmod.resolved_revalidation_window(1) == 1.0
    assert cmod.resolved_revalidation_window(1.5) == 1.5
    assert cmod.resolved_revalidation_window(10**300) == float(10**300)


def test_resolved_window_huge_int_overflow_is_configuration_error():
    huge = 10**10000
    with pytest.raises(ConfigurationError) as excinfo:
        cmod.resolved_revalidation_window(huge)
    assert isinstance(excinfo.value.__cause__, OverflowError)


# ---------------------------------------------------------------------------
# _host_validation_request - shape/lexical/absent vs null (no defect, but pinned)
# ---------------------------------------------------------------------------


def test_host_validation_absent_headers_and_server_uses_defaults():
    scope: dict = {}
    req = cmod._host_validation_request(scope)
    assert req.META["SERVER_NAME"] == "unknown"
    assert req.META["SERVER_PORT"] == "0"
    assert "HTTP_HOST" not in req.META


def test_host_validation_duplicate_hosts_are_comma_joined():
    scope = {"headers": [(b"host", b"a.com"), (b"host", b"b.com")], "server": ("x", 80)}
    req = cmod._host_validation_request(scope)
    assert req.META["HTTP_HOST"] == "a.com,b.com"


def test_host_validation_case_insensitive_header():
    scope = {"headers": [(b"Host", b"example.com")], "server": ("x", 80)}
    req = cmod._host_validation_request(scope)
    assert req.META["HTTP_HOST"] == "example.com"


def test_host_validation_server_absent_vs_null():
    for server in [
        None,
        0,
        False,
        "",
    ]:
        scope = {"headers": [], "server": server}
        req = cmod._host_validation_request(scope)  # type: ignore[arg-type]
        assert req.META["SERVER_NAME"] == "unknown"


# ---------------------------------------------------------------------------
# CancelledError propagation - every except (Cancelled...) must be hit
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
        await cmod.revalidate_operation_actor(HostileHandler())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_revalidate_hostile_ack_websocket_cancelled_propagates():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        @property
        def websocket(self):  # type: ignore[no-redef]
            raise asyncio.CancelledError("hostile websocket cancelled")

        view = Mock()

    with pytest.raises(asyncio.CancelledError):
        await cmod.revalidate_operation_actor(HostileHandler())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_revalidate_hostile_view_cancelled_propagates():
    class Handler:
        connection_acknowledged = True

        @property
        def view(self):
            raise asyncio.CancelledError("hostile view cancelled")

        websocket = Mock()

    with pytest.raises(asyncio.CancelledError):
        await cmod.revalidate_operation_actor(Handler())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_revalidate_hostile_revoked_cancelled_propagates():
    handler = Mock()
    handler.connection_acknowledged = True
    handler.view = Mock()
    handler.view.scope = _fresh_scope()
    # Make _revocation.revoked raise Cancelled
    type(handler.view._revocation).revoked = property(
        lambda self: (_ for _ in ()).throw(asyncio.CancelledError("cancelled")),
    )  # type: ignore[attr-defined]
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
        await cmod._actor_is_current(HostileConsumer())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_actor_get_propagates():
    class HostileScope(dict):
        def get(self, k, d=None):
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

    scope = {"user": HostileUser()}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_note_propagates():
    scope = {"user": Mock(is_authenticated=True)}
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
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope

    class HostileConsumer:
        @property
        def revalidation_window(self):
            raise asyncio.CancelledError("cancelled window")

        @property
        def scope(self):  # type: ignore[no-redef]
            return scope

    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(HostileConsumer())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_cache_comparison_propagates():
    class HostileFloat:
        def __gt__(self, other):
            raise asyncio.CancelledError("cancelled gt")

    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY].authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = HostileFloat()  # type: ignore[assignment]
    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_refreshed_propagates():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch.object(cmod, "_refreshed_actor", side_effect=asyncio.CancelledError("cancelled")):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_refreshed_is_auth_propagates():
    scope = {"user": Mock(is_authenticated=True)}
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
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0

    class HostileScope(dict):
        raise_enabled = False

        def __setitem__(self, k, v):
            if self.raise_enabled and k == "user":
                raise asyncio.CancelledError("cancelled set user")
            super().__setitem__(k, v)

    hostile_scope = HostileScope(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    hostile_scope["user"] = scope["user"]
    hostile_scope.raise_enabled = True
    consumer.scope = hostile_scope  # type: ignore[assignment]
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_cancelled_at_timestamp_set_propagates():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 10.0

    class HostileScope(dict):
        raise_enabled = False

        def __setitem__(self, k, v):
            if self.raise_enabled and k == cmod._REVALIDATED_AT_SCOPE_KEY:
                raise asyncio.CancelledError("cancelled timestamp")
            super().__setitem__(k, v)

    hostile_scope = HostileScope(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    hostile_scope["user"] = scope["user"]
    hostile_scope.raise_enabled = True
    consumer.scope = hostile_scope  # type: ignore[assignment]
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
        await cmod.send_revalidated_operation_frame(HostileWS(), {}, AsyncMock())  # type: ignore[arg-type]


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

        class HostileMessage(dict):
            def get(self, k, d=None):
                raise ValueError("hostile")

        # ValueError triggers the except that calls send_revalidated, which now raises Cancelled
        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json(HostileMessage({"type": "next"}))  # type: ignore[arg-type]


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
        await cmod._revoke_connection(HostileWS())  # type: ignore[arg-type]


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
# Extra coverage for remaining hostile branches (to reach 100%)
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

    result = await cmod.revalidate_operation_actor(HostileHandler())  # type: ignore[arg-type]
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
        result = await cmod.revalidate_operation_actor(HostileHandler())  # type: ignore[arg-type]
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
    )  # type: ignore[attr-defined]
    handler.websocket = Mock()
    handler.websocket.ws_consumer = handler.view
    with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock):
        result = await cmod.revalidate_operation_actor(handler)
        assert result is False
    # Restore
    type(handler.view._revocation).revoked = property(
        lambda self: self.state != cmod._REVOCATION_PERMITTED,
    )  # type: ignore[attr-defined]


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
async def test_actor_is_current_scope_get_hostile_value_error():
    class HostileScope(dict):
        def get(self, k, d=None):
            if k == "user":
                raise ValueError("hostile get")
            return super().get(k, d)

    scope = HostileScope()
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    result = await cmod._actor_is_current(consumer)
    assert result is False


@pytest.mark.asyncio
async def test_actor_is_current_connection_was_authenticated_hostile():
    scope = {"user": None}
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
async def test_actor_is_current_scope_user_set_hostile_value_error():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):

        class HostileScope(dict):
            raise_enabled = False

            def __setitem__(self, k, v):
                if self.raise_enabled and k == "user":
                    raise ValueError("hostile set user")
                super().__setitem__(k, v)

        hostile_scope = HostileScope(scope)
        hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
        hostile_scope["user"] = scope["user"]
        hostile_scope.raise_enabled = True
        consumer.scope = hostile_scope  # type: ignore[assignment]
        result = await cmod._actor_is_current(consumer)
        assert result is False


@pytest.mark.asyncio
async def test_send_revalidated_revoked_hostile():
    consumer = Mock()
    consumer.scope = _fresh_scope()
    # Make revoked raise
    type(consumer._revocation).revoked = property(
        lambda self: (_ for _ in ()).throw(ValueError("hostile")),
    )  # type: ignore[attr-defined]
    # Need to actually set _revocation to a real one with hostile property
    # Use a mock revocation
    mock_rev = Mock()
    type(mock_rev).revoked = property(lambda self: (_ for _ in ()).throw(ValueError("hostile")))  # type: ignore[attr-defined]
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

    async def hostile_send(msg):
        raise ValueError("hostile send")

    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, hostile_send)
        # Should have revoked, not raised
        assert consumer._revocation.revoked is True


@pytest.mark.asyncio
async def test_send_json_message_get_value_error_triggers_revoke():
    _, adapter = _build_consumer_and_adapter()
    adapter.ws_consumer.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(adapter.ws_consumer.scope)
    with patch.object(cmod, "_refreshed_actor", return_value=None):

        class HostileMessage(dict):
            def get(self, k, d=None):
                raise ValueError("hostile get")

        await adapter.send_json(HostileMessage({"type": "next"}))  # type: ignore[arg-type]
        assert adapter.ws_consumer._revocation.revoked is True


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
        # No raise, just suppressed


# ---------------------------------------------------------------------------
# Remaining coverage for 38 missing lines (hostile + Cancelled)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revalidate_ack_hostile_websocket_cancelled_inner():
    class HostileHandler:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        @property
        def websocket(self):
            raise asyncio.CancelledError("hostile websocket cancelled")

        view = Mock()

    with pytest.raises(asyncio.CancelledError):
        await cmod.revalidate_operation_actor(HostileHandler())  # type: ignore[arg-type]


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
            await cmod.revalidate_operation_actor(HostileHandler())  # type: ignore[arg-type]


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
async def test_actor_is_current_window_cancelled_at_cache():
    class HostileFloat:
        def __gt__(self, other):
            raise asyncio.CancelledError("cancelled gt")

    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY].authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = HostileFloat()  # type: ignore[assignment]
    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_refreshed_cancelled():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch.object(cmod, "_refreshed_actor", side_effect=asyncio.CancelledError("cancelled")):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_actor_is_current_scope_user_set_cancelled():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0

    class HostileScope(dict):
        raise_enabled = False

        def __setitem__(self, k, v):
            if self.raise_enabled and k == "user":
                raise asyncio.CancelledError("cancelled set user")
            super().__setitem__(k, v)

    hostile_scope = HostileScope(scope)
    hostile_scope[_ACTOR_STATE_SCOPE_KEY] = scope[_ACTOR_STATE_SCOPE_KEY]
    hostile_scope["user"] = scope["user"]
    hostile_scope.raise_enabled = True
    consumer.scope = hostile_scope  # type: ignore[assignment]
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


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

    async def hostile_send(msg):
        raise asyncio.CancelledError("cancelled send")

    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(ws, {"type": "next"}, hostile_send)


@pytest.mark.asyncio
async def test_send_json_message_get_cancelled():
    _, adapter = _build_consumer_and_adapter()
    with patch.object(
        cmod,
        "send_revalidated_operation_frame",
        side_effect=asyncio.CancelledError("cancelled"),
    ):

        class HostileMessage(dict):
            def get(self, k, d=None):
                raise ValueError("hostile get")

        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json(HostileMessage({"type": "next"}))  # type: ignore[arg-type]


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


@pytest.mark.asyncio
async def test_send_json_control_lease_cancelled():
    _, adapter = _build_consumer_and_adapter()
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=asyncio.CancelledError("cancelled lease"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json({"type": "ping"})


@pytest.mark.asyncio
async def test_send_json_revalidated_cancelled():
    _, adapter = _build_consumer_and_adapter()
    adapter.ws_consumer.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(adapter.ws_consumer.scope)
    with patch.object(
        cmod,
        "send_revalidated_operation_frame",
        side_effect=asyncio.CancelledError("cancelled"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await adapter.send_json({"type": "next"})


# utils/sessions extra
def test_utils_connection_actor_state_hostile_isinstance():
    class HostileState:
        pass

    # Make isinstance raise
    original_isinstance = (
        __builtins__["isinstance"] if isinstance(__builtins__, dict) else __builtins__.isinstance
    )  # type: ignore[attr-defined]

    def hostile_isinstance(a, b):
        if b is ConnectionActorState:
            raise ValueError("hostile isinstance")
        return original_isinstance(a, b)

    scope = {_ACTOR_STATE_SCOPE_KEY: HostileState()}
    with patch(
        "django_strawberry_framework.utils.sessions.isinstance",
        side_effect=ValueError("hostile"),
    ):
        with pytest.raises(ConfigurationError):
            connection_actor_state(scope)  # type: ignore[arg-type]


# More remaining coverage
@pytest.mark.asyncio
async def test_revalidate_outer_lease_cancelled_extra():
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
        side_effect=asyncio.CancelledError("cancelled"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.revalidate_operation_actor(handler)


@pytest.mark.asyncio
async def test_actor_is_current_window_cancelled_extra():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope

    class HC:
        @property
        def revalidation_window(self):
            raise asyncio.CancelledError("cancelled")

        @property
        def scope(self):
            return scope

    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(HC())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_actor_is_current_cache_cancelled():
    class HF:
        def __gt__(self, other):
            raise asyncio.CancelledError("cancelled")

    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY].authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = HF()  # type: ignore[assignment]
    with pytest.raises(asyncio.CancelledError):
        await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_send_revalidated_actor_lease_cancelled():
    consumer = Mock()
    consumer.scope = _fresh_scope()
    ws = Mock()
    ws.ws_consumer = consumer
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=asyncio.CancelledError("cancelled"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod.send_revalidated_operation_frame(ws, {}, AsyncMock())


@pytest.mark.asyncio
async def test_send_json_message_get_hostile_value_error():
    _, adapter = _build_consumer_and_adapter()
    adapter.ws_consumer.scope["user"] = Mock(is_authenticated=True)
    from django_strawberry_framework.utils.sessions import note_authenticated_actor

    note_authenticated_actor(adapter.ws_consumer.scope)
    with patch.object(cmod, "_refreshed_actor", return_value=None):

        class HM(dict):
            def get(self, k, d=None):
                raise ValueError("hostile")

        await adapter.send_json(HM({"type": "next"}))  # type: ignore[arg-type]
        assert adapter.ws_consumer._revocation.revoked is True


def test_utils_hostile_isinstance_value_error():
    scope = {_ACTOR_STATE_SCOPE_KEY: object()}
    with patch(
        "django_strawberry_framework.utils.sessions.isinstance",
        side_effect=ValueError("hostile"),
    ):
        with pytest.raises(ConfigurationError):
            connection_actor_state(scope)  # type: ignore[arg-type]


def test_utils_hostile_get_value_error():
    class HS(dict):
        def get(self, k, d=None):
            raise ValueError("hostile get")

    with pytest.raises(ConfigurationError):
        connection_actor_state(HS())  # type: ignore[arg-type]


def test_utils_hostile_setitem_value_error():
    class HS(dict):
        def __setitem__(self, k, v):
            raise ValueError("hostile set")

    with pytest.raises(ConfigurationError):
        connection_actor_state(HS())  # type: ignore[arg-type]


# Additional remaining coverage
@pytest.mark.asyncio
async def test_revalidate_ack_websocket_value_error_inner():
    class H:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        @property
        def websocket(self):
            raise ValueError("hostile ws")

        view = Mock()

    result = await cmod.revalidate_operation_actor(H())  # type: ignore[arg-type]
    assert result is False


@pytest.mark.asyncio
async def test_revalidate_ack_revoke_value_error():
    class H:
        @property
        def connection_acknowledged(self):
            raise ValueError("hostile ack")

        websocket = Mock()
        view = Mock()

    with patch.object(cmod, "_revoke_connection", side_effect=ValueError("hostile revoke")):
        result = await cmod.revalidate_operation_actor(H())  # type: ignore[arg-type]
        assert result is False


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
async def test_actor_is_current_window_value_error_fallthrough():
    class HF:
        def __gt__(self, other):
            raise ValueError("hostile gt")

    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    scope[_ACTOR_STATE_SCOPE_KEY].authenticated_provenance = True
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = HF()  # type: ignore[assignment]
    with patch.object(cmod, "_refreshed_actor", return_value=Mock(is_authenticated=True)):
        result = await cmod._actor_is_current(consumer)
        assert result is True


@pytest.mark.asyncio
async def test_actor_is_current_connection_was_authenticated_cancelled():
    scope = {"user": None}
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


@pytest.mark.asyncio
async def test_actor_is_current_note_cancelled():
    scope = {"user": Mock(is_authenticated=True)}
    scope[_ACTOR_STATE_SCOPE_KEY] = ConnectionActorState()
    consumer = Mock()
    consumer.scope = scope
    consumer.revalidation_window = 0.0
    with patch(
        "django_strawberry_framework.consumers.note_authenticated_actor",
        side_effect=asyncio.CancelledError("cancelled"),
    ):
        with pytest.raises(asyncio.CancelledError):
            await cmod._actor_is_current(consumer)


@pytest.mark.asyncio
async def test_send_revalidated_revoked_value_error():
    consumer = Mock()
    mock_rev = Mock()
    type(mock_rev).revoked = property(
        lambda self: (_ for _ in ()).throw(ValueError("hostile revoked")),
    )  # type: ignore[attr-defined]
    consumer._revocation = mock_rev
    consumer.scope = _fresh_scope()
    consumer.revalidation_window = 0.0
    ws = Mock()
    ws.ws_consumer = consumer
    with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock):
        await cmod.send_revalidated_operation_frame(ws, {}, AsyncMock())
        # Should not raise


@pytest.mark.asyncio
async def test_send_revalidated_is_current_value_error():
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
        with patch.object(cmod, "_revoke_connection", new_callable=AsyncMock) as mr:
            await cmod.send_revalidated_operation_frame(ws, {}, AsyncMock())
            mr.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_json_control_lease_value_error():
    _, adapter = _build_consumer_and_adapter()
    with patch(
        "django_strawberry_framework.consumers.actor_lease",
        side_effect=ValueError("hostile"),
    ):
        await adapter.send_json({"type": "ping"})
        # Should not raise, just suppress


@pytest.mark.asyncio
async def test_send_json_control_send_value_error():
    _, adapter = _build_consumer_and_adapter()
    with patch.object(
        adapter.__class__.__bases__[0],
        "send_json",
        side_effect=ValueError("hostile"),
    ):
        await adapter.send_json({"type": "ping"})


def test_utils_hostile_scope_get_isinstance_value_error():
    class HS(dict):
        def get(self, k, d=None):
            if k == _ACTOR_STATE_SCOPE_KEY:
                return object()
            return super().get(k, d)

    # Make isinstance raise
    with patch(
        "django_strawberry_framework.utils.sessions.isinstance",
        side_effect=ValueError("hostile"),
    ):
        with pytest.raises(ConfigurationError):
            connection_actor_state(HS())  # type: ignore[arg-type]
