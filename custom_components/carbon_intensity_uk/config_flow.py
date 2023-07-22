"""Adds config flow for Carbon Intensity."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

from .client import Client as CarbonIntentisityApi
from .const import CONF_POSTCODE, DOMAIN, PLATFORMS  # pylint: disable=unused-import


class CarbonIntensityFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Carbon Intensity UK."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(
        self, user_input=None  # pylint: disable=bad-continuation
    ):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(user_input[CONF_POSTCODE])
            if valid:
                _LOGGER.debug("Input is valid")
                return self.async_create_entry(
                    title=user_input[CONF_POSTCODE], data=user_input
                )
            else:
                _LOGGER.debug("Input not valid")
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CarbonIntensityOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POSTCODE): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, postcode):
        """Return true if credentials is valid."""
        try:
            client = CarbonIntentisityApi(postcode)
            await client.async_get_data()
            _LOGGER.debug("Input successfully")
            return True
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.debug(exception)
        _LOGGER.debug("Oops! Input failed!")
        return False


class CarbonIntensityOptionsFlowHandler(config_entries.OptionsFlow):
    """Carbon Intensity UK config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_POSTCODE), data=self.options
        )
