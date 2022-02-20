"""DataUpdateCoordinator for the Radio Browser integration."""
from __future__ import annotations

from typing import Any

from pyradios import RadioBrowser

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, SCAN_INTERVAL


class RadioBrowserDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """The Radio Browser Data Update Coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the Radio Browser coordinator."""
        self.radios = RadioBrowser()
        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch stats from Radio Browser."""
        endpoint = self.radios.build_url("json/stats")
        result: dict[str, Any] | None = await self.hass.async_add_executor_job(
            self.radios.client.get, endpoint
        )
        if not result:
            raise UpdateFailed("Failed to fetch data from Radio Browser")
        return result
