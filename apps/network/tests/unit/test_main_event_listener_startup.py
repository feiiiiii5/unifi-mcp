"""Startup of the network websocket event listener (#680).

The listener owns the backoff/reconnect loop, which treats "not connected"
as a normal state — so startup must not depend on the boot connect
succeeding. These tests prove the listener starts after a failed
``initialize()`` (the network-free half of the issue; the recovery half
needs live hardware) without importing any more of the app than the helper.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


def _config(websocket_enabled=True):
    return SimpleNamespace(
        network=SimpleNamespace(events={"websocket_enabled": websocket_enabled})
    )


@pytest.mark.asyncio
async def test_listener_starts_despite_failed_boot_connect():
    """#680: a failed initialize() must not strand listening=false forever."""
    from unifi_network_mcp.main import start_event_listener_if_enabled

    event_manager = SimpleNamespace(start_listening=AsyncMock())
    started = await start_event_listener_if_enabled(
        config=_config(True), event_manager=event_manager
    )
    assert started is True
    event_manager.start_listening.assert_awaited_once()


@pytest.mark.asyncio
async def test_listener_stays_off_when_disabled():
    from unifi_network_mcp.main import start_event_listener_if_enabled

    event_manager = SimpleNamespace(start_listening=AsyncMock())
    started = await start_event_listener_if_enabled(
        config=_config(False), event_manager=event_manager
    )
    assert started is False
    event_manager.start_listening.assert_not_awaited()


@pytest.mark.asyncio
async def test_listener_start_failure_is_logged_not_raised():
    from unifi_network_mcp.main import start_event_listener_if_enabled

    event_manager = SimpleNamespace(
        start_listening=AsyncMock(side_effect=RuntimeError("boom"))
    )
    started = await start_event_listener_if_enabled(
        config=_config(True), event_manager=event_manager
    )
    assert started is False