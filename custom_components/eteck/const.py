"""Constants for the Eteck integration."""

from typing import Final

DOMAIN: Final = "eteck"

CONF_PROJECT: Final = "project"

CURRENCY: Final = "EUR"

FIXED_MONTHLY: Final = "fixed_monthly"
VARIABLE: Final = "variable"

# Tariff keys allowed in tariffs.yaml, mapped to the unit of the sensor.
FIXED_MONTHLY_KEYS: Final = ("heat_pump_rental", "metering", "cooling", "heating")
VARIABLE_UNITS: Final = {
    "heating_per_gj": f"{CURRENCY}/GJ",
    "hot_water_per_m3": f"{CURRENCY}/m³",
}
UNIT_PER_MONTH: Final = f"{CURRENCY}/month"
