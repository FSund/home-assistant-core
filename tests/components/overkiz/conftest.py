"""Configuration for overkiz tests."""
from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.components.overkiz.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.overkiz import load_setup_fixture
from tests.components.overkiz.test_config_flow import (
    TEST_EMAIL,
    TEST_GATEWAY_ID,
    TEST_HUB,
    TEST_PASSWORD,
)

MOCK_SETUP_RESPONSE = Mock(devices=[], gateways=[])


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Somfy TaHoma Switch",
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD, "hub": TEST_HUB},
    )


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.overkiz.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up the Overkiz integration for testing."""
    mock_config_entry.add_to_hass(hass)

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_setup=AsyncMock(return_value=load_setup_fixture()),
        get_scenarios=AsyncMock(return_value=[]),
        fetch_events=AsyncMock(return_value=[]),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry
