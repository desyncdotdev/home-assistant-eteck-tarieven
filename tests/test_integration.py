"""Test the config flow and sensors."""

from datetime import datetime

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant, State
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache_with_extra_data,
)

from custom_components.eteck.const import CONF_PROJECT, DOMAIN
from custom_components.eteck.sensor import fixed_costs_between
from custom_components.eteck.tariffs import load_projects

PROJECT = "keijzershof-en-tuindershof-pijnacker-nootdorp"
PREFIX = "sensor.eteck_keijzershof_en_tuindershof_pijnacker_nootdorp"


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=PROJECT, data={CONF_PROJECT: PROJECT})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert "issues/new?template=tariffs.yml" in result["description_placeholders"]["issue_url"]
    assert "CONTRIBUTING.md" in result["description_placeholders"]["contributing_url"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROJECT: PROJECT}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Keijzershof en Tuindershof, Pijnacker-Nootdorp"
    assert result["data"] == {CONF_PROJECT: PROJECT}

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROJECT: PROJECT}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.freeze_time("2026-06-01 12:00:00+00:00")
async def test_sensors(hass: HomeAssistant):
    await _setup(hass)

    expected = {
        "heat_pump_rental_per_month": ("14.88", "EUR"),
        "metering_fee_per_month": ("2.81", "EUR"),
        "fixed_costs_cooling_per_month": ("18.18", "EUR"),
        "fixed_costs_heating_per_month": ("51.31", "EUR"),
        "total_fixed_costs_per_month": ("87.18", "EUR"),
        "heating_price": ("40.97", "EUR/GJ"),
        "hot_water_price": ("6.88", "EUR/m³"),
    }
    for name, (value, unit) in expected.items():
        state = hass.states.get(f"{PREFIX}_{name}")
        assert state is not None, name
        assert state.state == value
        assert state.attributes["unit_of_measurement"] == unit
        assert state.attributes["tariff_year"] == 2026
        assert state.attributes.get("device_class") == ("monetary" if unit == "EUR" else None)

    accumulated = hass.states.get(f"{PREFIX}_accumulated_fixed_costs")
    assert accumulated.state == "0.0"
    assert accumulated.attributes["unit_of_measurement"] == "EUR"
    assert accumulated.attributes["device_class"] == "monetary"
    assert accumulated.attributes["state_class"] == "total"
    assert len(hass.states.async_all("sensor")) == len(expected) + 1
    assert not ir.async_get(hass).issues


@pytest.mark.freeze_time("2027-02-01 12:00:00+00:00")
async def test_missing_year_falls_back_and_raises_issue(hass: HomeAssistant):
    await _setup(hass)

    state = hass.states.get(f"{PREFIX}_heating_price")
    assert state.state == "40.97"
    assert state.attributes["tariff_year"] == 2026
    assert ir.async_get(hass).async_get_issue(DOMAIN, f"outdated_tariffs_{PROJECT}")


async def test_refreshes_at_midnight(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 12, 31, 23, 59, 30, tzinfo=dt_util.DEFAULT_TIME_ZONE))
    await _setup(hass)
    before = hass.states.get(f"{PREFIX}_heating_price").last_reported

    midnight = datetime(2027, 1, 1, 0, 0, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE)
    freezer.move_to(midnight)
    async_fire_time_changed(hass, midnight)
    await hass.async_block_till_done()
    assert hass.states.get(f"{PREFIX}_heating_price").last_reported > before


def _local(*args: int) -> datetime:
    return datetime(*args, tzinfo=dt_util.DEFAULT_TIME_ZONE)


async def test_fixed_costs_between(hass: HomeAssistant):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    project = load_projects()[PROJECT]

    # A whole month costs the monthly total, whatever its length (and DST).
    assert fixed_costs_between(project, _local(2026, 2, 1), _local(2026, 3, 1)) == 87.18
    assert fixed_costs_between(project, _local(2026, 3, 1), _local(2026, 4, 1)) == 87.18
    # One day of a 30 day month, and a period spanning two months.
    one_day = fixed_costs_between(project, _local(2026, 6, 10), _local(2026, 6, 11))
    assert one_day == pytest.approx(87.18 / 30)
    spanning = fixed_costs_between(project, _local(2026, 6, 16), _local(2026, 8, 1))
    assert spanning == pytest.approx(87.18 * 1.5)
    assert fixed_costs_between(project, _local(2026, 6, 2), _local(2026, 6, 1)) == 0


async def test_accumulates_every_hour(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(_local(2026, 6, 1, 0, 0, 0))
    await _setup(hass)
    entity_id = f"{PREFIX}_accumulated_fixed_costs"
    assert hass.states.get(entity_id).state == "0.0"

    for hour in (1, 2):
        freezer.move_to(_local(2026, 6, 1, hour, 0, 0))
        async_fire_time_changed(hass, _local(2026, 6, 1, hour, 0, 0))
        await hass.async_block_till_done()
    assert float(hass.states.get(entity_id).state) == pytest.approx(87.18 / 30 / 24 * 2, abs=1e-4)


async def test_accumulated_costs_survive_a_restart(hass: HomeAssistant, freezer):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(_local(2026, 7, 1, 0, 0, 0))
    stored = {"value": 100.0, "until": _local(2026, 6, 1, 0, 0, 0).isoformat()}
    mock_restore_cache_with_extra_data(
        hass, [(State(f"{PREFIX}_accumulated_fixed_costs", "100.0"), stored)]
    )
    await _setup(hass)

    # Continues from the stored value and catches up on the month it missed.
    state = hass.states.get(f"{PREFIX}_accumulated_fixed_costs")
    assert float(state.state) == pytest.approx(187.18)


async def test_unload(hass: HomeAssistant):
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
