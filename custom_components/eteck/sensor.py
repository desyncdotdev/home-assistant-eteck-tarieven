"""Sensors exposing the Eteck tariffs of the current year."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.restore_state import ExtraStoredData, RestoreEntity
from homeassistant.util import dt as dt_util

from . import EteckConfigEntry
from .const import CURRENCY, DOMAIN, VARIABLE_UNITS
from .tariffs import Project, YearTariffs

TOTAL = "fixed_monthly_total"
ACCUMULATED = "fixed_costs_accumulated"


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
            CURRENCY,
            lambda tariffs, key=key: tariffs.fixed_monthly.get(key),
        )
        for key in sorted(fixed)
    ]
    if fixed:
        entities.append(
            EteckTariffSensor(project, TOTAL, CURRENCY, lambda t: t.fixed_monthly_total)
        )
        entities.append(EteckAccumulatedFixedCostsSensor(project))
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


def _device_info(project: Project) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, project.key)},
        name=f"Eteck {project.name}",
        manufacturer="Eteck",
        entry_type=DeviceEntryType.SERVICE,
    )


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
        if unit == CURRENCY:
            self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_device_info = _device_info(project)

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


def _next_month(moment: datetime) -> datetime:
    """Return the start of the month after the one `moment` is in."""
    first = moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return (first + timedelta(days=32)).replace(day=1)


def fixed_costs_between(project: Project, start: datetime, end: datetime) -> float:
    """Return the fixed costs for a period, charging every month pro rata."""
    start, end = dt_util.as_local(start), dt_util.as_local(end)
    costs = 0.0
    while start < end:
        month_end = _next_month(start)
        month_start = month_end.replace(day=1, month=start.month, year=start.year)
        until = min(end, month_end)
        monthly = project.tariffs_for(start.year).fixed_monthly_total
        costs += monthly * (until - start) / (month_end - month_start)
        start = until
    return costs


@dataclass
class AccumulatedData(ExtraStoredData):
    """The accumulated costs and the moment up to which they are charged."""

    value: float
    until: datetime

    def as_dict(self) -> dict[str, Any]:
        """Return a dict that can be stored."""
        return {"value": self.value, "until": self.until.isoformat()}


class EteckAccumulatedFixedCostsSensor(RestoreEntity, SensorEntity):
    """The fixed costs paid so far, growing a little every hour.

    A total in EUR is what the Energy dashboard needs to track costs.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = ACCUMULATED
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY
    _attr_suggested_display_precision = 2

    def __init__(self, project: Project) -> None:
        """Initialize the sensor."""
        self._project = project
        self._value = 0.0
        self._until = dt_util.utcnow()
        self._attr_unique_id = f"{project.key}_{ACCUMULATED}"
        self._attr_device_info = _device_info(project)

    @property
    def native_value(self) -> float:
        """Return the fixed costs accumulated since the sensor was added."""
        return round(self._value, 4)

    @property
    def extra_restore_state_data(self) -> AccumulatedData:
        """Return the data to continue from after a restart."""
        return AccumulatedData(self._value, self._until)

    @callback
    def _accumulate(self) -> None:
        now = dt_util.utcnow()
        self._value += fixed_costs_between(self._project, self._until, now)
        self._until = now

    async def async_added_to_hass(self) -> None:
        """Continue where we left off, including the time we were not running."""
        if (stored := await self.async_get_last_extra_data()) is not None:
            data = stored.as_dict()
            until = dt_util.parse_datetime(str(data.get("until")))
            if until is not None and isinstance(data.get("value"), int | float):
                self._value, self._until = float(data["value"]), until
                self._accumulate()

        @callback
        def _update(_: datetime) -> None:
            self._accumulate()
            self.async_write_ha_state()

        self.async_on_remove(async_track_time_change(self.hass, _update, minute=0, second=0))
