"""Expose Radio Browser as a media source."""
from __future__ import annotations

from functools import partial

import pycountry

from homeassistant.components.media_player.const import (
    MEDIA_CLASS_CHANNEL,
    MEDIA_CLASS_DIRECTORY,
    MEDIA_CLASS_MUSIC,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_URL,
)
from homeassistant.components.media_player.errors import BrowseError
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER
from .coordinator import RadioBrowserDataUpdateCoordinator

CODEC_TO_MIMETYPE = {
    "MP3": "audio/mpeg",
    "AAC": "audio/mp4",
    "AAC+": "audio/mp4",
    "OGG": "audio/ogg",
}


async def async_get_media_source(hass: HomeAssistant) -> RadioMediaSource:
    """Set up Radio Browser media source."""
    # Radio browser support only a single config entry
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    coordinator = hass.data[DOMAIN][entry.entry_id]

    return RadioMediaSource(hass, coordinator)


class RadioMediaSource(MediaSource):
    """Provide Radio stations as media sources."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: RadioBrowserDataUpdateCoordinator,
    ) -> None:
        """Initialize CameraMediaSource."""
        super().__init__(DOMAIN)
        self.hass = hass
        self.name = coordinator.config_entry.title
        self.coordinator = coordinator

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve selected Radio station to a streaming URL."""
        stations = await self.hass.async_add_executor_job(
            self.coordinator.radios.station_by_uuid, item.identifier
        )
        if not stations:
            raise BrowseError("Radio station is no longer available")
        station = stations[0]

        mime_type = CODEC_TO_MIMETYPE.get(station["codec"])
        if not mime_type:
            raise BrowseError("Could not determine stream type of radio station")

        return PlayMedia(station["url"], mime_type)

    async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Return media."""
        root = BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MEDIA_CLASS_CHANNEL,
            media_content_type=MEDIA_TYPE_MUSIC,
            title=self.name,
            can_play=False,
            can_expand=True,
            children_media_class=MEDIA_CLASS_DIRECTORY,
        )
        root.children = []

        # Browsing stations
        if item.identifier:
            stations = []
            if item.identifier == "popular":
                stations = await self.hass.async_add_executor_job(
                    partial(
                        self.coordinator.radios.search,
                        hidebroken=True,
                        limit=256,
                        order="clickcount",
                        reverse=True,
                    )
                )
            else:
                stations = await self.hass.async_add_executor_job(
                    partial(
                        self.coordinator.radios.stations_by_countrycode,
                        item.identifier,
                        hidebroken=True,
                        order="clickcount",
                        reverse=True,
                    )
                )

            if stations:
                for station in stations:
                    LOGGER.error(station)
                    station = BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=station["stationuuid"],
                        media_class=MEDIA_CLASS_MUSIC,
                        media_content_type=MEDIA_TYPE_URL,
                        title=station["name"],
                        can_play=True,
                        can_expand=False,
                        thumbnail=station["favicon"],
                    )
                    root.children.append(station)
            return root

        popular = BrowseMediaSource(
            domain=DOMAIN,
            identifier="popular",
            media_class=MEDIA_CLASS_DIRECTORY,
            media_content_type=MEDIA_TYPE_MUSIC,
            title="Popular",
            can_play=False,
            can_expand=True,
        )
        root.children.append(popular)

        if countries := await self.hass.async_add_executor_job(
            self.coordinator.radios.countrycodes
        ):
            for country in countries:
                country_info = pycountry.countries.get(alpha_2=country["name"])
                if not country_info:
                    continue
                country_source = BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=country["name"],
                    media_class=MEDIA_CLASS_DIRECTORY,
                    media_content_type=MEDIA_TYPE_MUSIC,
                    title=country_info.name,
                    can_play=False,
                    can_expand=True,
                    thumbnail=f"https://flagcdn.com/256x192/{country['name'].lower()}.png",
                )
                root.children.append(country_source)

        return root
