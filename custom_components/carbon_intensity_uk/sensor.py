"""Sensor platform for carbon intensity UK."""
from custom_components.carbon_intensity_uk.const import (
    DEFAULT_NAME,
    DOMAIN,
    ICON,
    HIGH_ICON,
    LOW_ICON,
    MODERATE_ICON,
    SENSOR,
    INTENSITY,
)
from custom_components.carbon_intensity_uk.entity import CarbonIntensityEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([CarbonIntensitySensor(coordinator, entry)])


class CarbonIntensitySensor(CarbonIntensityEntity):
    """Carbon Intensity Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("current_period_index")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        index = self.coordinator.data.get("current_period_index")
        intensity = INTENSITY[index]
        if intensity >= INTENSITY["high"]:
            return HIGH_ICON
        elif intensity == INTENSITY["moderate"]:
            return MODERATE_ICON
        elif intensity <= INTENSITY["low"]:
            return LOW_ICON
        else:
            return ICON
