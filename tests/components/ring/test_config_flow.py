"""Test the Ring config flow."""
from unittest.mock import AsyncMock, Mock

import pytest
import ring_doorbell

from homeassistant import config_entries
from homeassistant.components.ring import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_ring_auth: Mock,
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"username": "hello@home-assistant.io", "password": "test-password"},
    )
    await hass.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "hello@home-assistant.io"
    assert result2["data"] == {
        "username": "hello@home-assistant.io",
        "token": {"access_token": "mock-token"},
    }
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    ("error_type", "errors_msg"),
    [
        (ring_doorbell.AuthenticationError, "invalid_auth"),
        (Exception, "unknown"),
    ],
    ids=["invalid-auth", "unknown-error"],
)
async def test_form_error(
    hass: HomeAssistant, mock_ring_auth: Mock, error_type, errors_msg
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_ring_auth.fetch_token.side_effect = error_type
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"username": "hello@home-assistant.io", "password": "test-password"},
    )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": errors_msg}


async def test_form_2fa(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_ring_auth: Mock,
) -> None:
    """Test form flow for 2fa."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    mock_ring_auth.fetch_token.side_effect = ring_doorbell.Requires2FAError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "foo@bar.com",
            CONF_PASSWORD: "fake-password",
        },
    )
    await hass.async_block_till_done()
    mock_ring_auth.fetch_token.assert_called_once_with(
        "foo@bar.com", "fake-password", None
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "2fa"
    mock_ring_auth.fetch_token.reset_mock(side_effect=True)
    mock_ring_auth.fetch_token.return_value = "new-foobar"
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={"2fa": "123456"},
    )

    mock_ring_auth.fetch_token.assert_called_once_with(
        "foo@bar.com", "fake-password", "123456"
    )
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "foo@bar.com"
    assert result3["data"] == {
        "username": "foo@bar.com",
        "token": "new-foobar",
    }
    assert len(mock_setup_entry.mock_calls) == 1
