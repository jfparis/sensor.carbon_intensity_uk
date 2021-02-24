"""
Custom integration to integrate UK Carbon Intensity API with Home Assistant.

For more details about this integration, please refer to
https://github.com/jscruz/sensor.carbon_intensity_uk
"""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from carbonintensity.client import Client as CarbonIntentisityApi

from .const import (
    CONF_POSTCODE,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(seconds=600)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    postcode = entry.data.get(CONF_POSTCODE)
    _LOGGER.debug("Postcode setup: %s" % postcode)

    coordinator = CarbonIntensityDataUpdateCoordinator(hass, postcode=postcode)
    _LOGGER.debug("Coordinator refresh triggered")
    await coordinator.async_refresh()
    _LOGGER.debug("Coordinator refresh completed")

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            _LOGGER.debug("Found platform %s" % platform)
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


class CarbonIntensityDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, postcode):
        """Initialize."""
        self.api = CarbonIntentisityApi(postcode)
        self.platforms = []

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            _LOGGER.debug("Coordinator update data async")
            data = await self.api.async_get_data()
            _LOGGER.debug("Coordinator update done")
            return data.get("data", {})
        except Exception as exception:
            raise UpdateFailed(exception)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
