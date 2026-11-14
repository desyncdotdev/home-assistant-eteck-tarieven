"""Sensors exposing the Eteck tariffs of the current year."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from . import EteckConfigEntry
from .const import DOMAIN, UNIT_PER_MONTH, VARIABLE_UNITS
from .tariffs import Project, YearTariffs

TOTAL = "fixed_monthly_total"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EteckConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create a sensor for every tariff the project has in any year."""
    project = entry.runtime_data
    fixed = {key for year in project.years.values() for key in year.fixed_monthly}
    variable = {key for year in project.years.values() for key in year.variable}

    entities = [
        EteckTariffSensor(
            project,
            f"fixed_{key}",
            UNIT_PER_MONTH,
            lambda tariffs, key=key: tariffs.fixed_monthly.get(key),
        )
        for key in sorted(fixed)
    ]
    if fixed:
        entities.append(
            EteckTariffSensor(project, TOTAL, UNIT_PER_MONTH, lambda t: t.fixed_monthly_total)
        )
    entities.extend(
        EteckTariffSensor(
            project,
            key,
            VARIABLE_UNITS[key],
            lambda tariffs, key=key: tariffs.variable.get(key),
        )
        for key in sorted(variable)
    )
    async_add_entities(entities)


class EteckTariffSensor(SensorEntity):
    """A single tariff, following the calendar year."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        project: Project,
        key: str,
        unit: str,
        value_fn: Callable[[YearTariffs], float | None],
    ) -> None:
        """Initialize the sensor."""
        self._project = project
        self._value_fn = value_fn
        self._attr_translation_key = key
        self._attr_unique_id = f"{project.key}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, project.key)},
            name=f"Eteck {project.name}",
            manufacturer="Eteck",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _tariffs(self) -> YearTariffs:
        return self._project.tariffs_for(dt_util.now().year)

    @property
    def native_value(self) -> float | None:
        """Return the tariff for the current year."""
        return self._value_fn(self._tariffs)

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        """Return the year the tariff was taken from."""
        return {"tariff_year": self._tariffs.year}

    async def async_added_to_hass(self) -> None:
        """Refresh at midnight so a new year's tariffs are picked up."""

        @callback
        def _refresh(_: datetime) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_time_change(self.hass, _refresh, hour=0, minute=0, second=0)
        )
