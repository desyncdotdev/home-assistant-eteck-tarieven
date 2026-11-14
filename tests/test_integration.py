"""Test the config flow and sensors."""

from datetime import datetime

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.eteck.const import CONF_PROJECT, DOMAIN

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
        "heat_pump_rental": ("14.88", "EUR/month"),
        "metering_fee": ("2.81", "EUR/month"),
        "fixed_costs_cooling": ("18.18", "EUR/month"),
        "fixed_costs_heating": ("51.31", "EUR/month"),
        "total_fixed_costs": ("87.18", "EUR/month"),
        "heating_price": ("40.97", "EUR/GJ"),
        "hot_water_price": ("6.88", "EUR/m³"),
    }
    for name, (value, unit) in expected.items():
        state = hass.states.get(f"{PREFIX}_{name}")
        assert state is not None, name
        assert state.state == value
        assert state.attributes["unit_of_measurement"] == unit
        assert state.attributes["tariff_year"] == 2026
    assert len(hass.states.async_all("sensor")) == len(expected)
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


async def test_unload(hass: HomeAssistant):
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
