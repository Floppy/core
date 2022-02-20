"""Support for Radio Browser sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RadioBrowserDataUpdateCoordinator


@dataclass
class RadioBrowserSensorEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[dict[str, Any]], int | None]


@dataclass
class RadioBrowserSensorEntityDescription(
    SensorEntityDescription, RadioBrowserSensorEntityDescriptionMixin
):
    """Describes a Radio Browser sensor entity."""


SENSORS: tuple[RadioBrowserSensorEntityDescription, ...] = (
    RadioBrowserSensorEntityDescription(
        key="stations",
        name="Stations",
        icon="mdi:radio",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda stats: stats.get("stations"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Radio Browser sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        RadioBrowserSensorEntity(
            coordinator=coordinator,
            description=description,
        )
        for description in SENSORS
    )


class RadioBrowserSensorEntity(CoordinatorEntity, SensorEntity):
    """Defines a Radio Browser sensor."""

    entity_description: RadioBrowserSensorEntityDescription

    def __init__(
        self,
        *,
        coordinator: RadioBrowserDataUpdateCoordinator,
        description: RadioBrowserSensorEntityDescription,
    ) -> None:
        """Initialize an Radio Browser sensor."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            configuration_url="https://www.radio-browser.info",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer="Radio-Browser.info",
            name=coordinator.config_entry.title,
            sw_version=coordinator.data.get("software_version"),
        )

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
