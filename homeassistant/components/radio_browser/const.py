"""Constants for the Radio Browser integration."""

from datetime import timedelta
import logging
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "radio_browser"
PLATFORMS: Final = [Platform.SENSOR]

LOGGER = logging.getLogger(__package__)

SCAN_INTERVAL: Final = timedelta(hours=1)
