"""The Eteck integration: fixed tariffs of Eteck heat networks as sensors."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util

from .const import CONF_PROJECT, DOMAIN
from .tariffs import Project, load_projects

PLATFORMS = [Platform.SENSOR]

type EteckConfigEntry = ConfigEntry[Project]


async def async_setup_entry(hass: HomeAssistant, entry: EteckConfigEntry) -> bool:
    """Set up Eteck from a config entry."""
    projects = await hass.async_add_executor_job(load_projects)
    if (project := projects.get(entry.data[CONF_PROJECT])) is None:
        raise ConfigEntryError(f"Project {entry.data[CONF_PROJECT]} is no longer in tariffs.yaml")
    entry.runtime_data = project

    year = dt_util.now().year
    issue_id = f"outdated_tariffs_{project.key}"
    if (used := project.tariffs_for(year).year) != year:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="outdated_tariffs",
            translation_placeholders={
                "project": project.name,
                "year": str(year),
                "used_year": str(used),
            },
            learn_more_url=(
                "https://github.com/desyncdotdev/home-assistant-eteck-tarieven/blob/main/CONTRIBUTING.md"
            ),
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, issue_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EteckConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
