"""Config flow for the Eteck integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_PROJECT, DOMAIN
from .tariffs import load_projects


class EteckConfigFlow(ConfigFlow, domain=DOMAIN):
    """Let the user pick their Eteck project."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the project selection."""
        projects = await self.hass.async_add_executor_job(load_projects)

        if user_input is not None:
            project = projects[user_input[CONF_PROJECT]]
            await self.async_set_unique_id(project.key)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=project.name, data={CONF_PROJECT: project.key})

        options = [
            SelectOptionDict(value=project.key, label=project.name)
            for project in sorted(projects.values(), key=lambda p: p.name.casefold())
        ]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROJECT): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
        )
