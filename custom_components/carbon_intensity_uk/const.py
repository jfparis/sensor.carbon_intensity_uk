"""Constants for carbon intensity."""
# Base component constants
NAME = "Carbon Intensity UK"
DOMAIN = "carbon_intensity_uk"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"

ISSUE_URL = "https://github.com/custom-components/sensor.carbon_intensity_uk/issues"

# Icons
ICON = "mdi:leaf"
LOW_ICON = "mdi:leaf"
MODERATE_ICON = "mdi:factory"
HIGH_ICON = "mdi:smog"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_POSTCODE = "postcode"
CONF_TARGET = "target"

# Defaults
DEFAULT_NAME = DOMAIN

INTENSITY = {
    "very_low" : 0,
    "low" : 1,
    "moderate": 2,
    "high": 3,
    "very_high": 4,
}

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
