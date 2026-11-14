"""Loading and validation of the bundled tariffs.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import voluptuous as vol
import yaml

from .const import FIXED_MONTHLY, FIXED_MONTHLY_KEYS, VARIABLE, VARIABLE_UNITS

TARIFFS_FILE = Path(__file__).parent / "tariffs.yaml"

_AMOUNT = vol.All(vol.Any(int, float), vol.Coerce(float), vol.Range(min=0))

_YEAR_SCHEMA = vol.Schema(
    {
        vol.Optional(FIXED_MONTHLY, default=dict): {vol.In(FIXED_MONTHLY_KEYS): _AMOUNT},
        vol.Optional(VARIABLE, default=dict): {vol.In(tuple(VARIABLE_UNITS)): _AMOUNT},
    }
)

_SCHEMA = vol.Schema(
    {
        vol.Match(r"^[a-z0-9]+(-[a-z0-9]+)*$"): {
            vol.Required("name"): vol.All(str, vol.Length(min=1)),
            vol.Required("years"): vol.All(
                {vol.All(int, vol.Range(min=2000, max=2100)): _YEAR_SCHEMA},
                vol.Length(min=1),
            ),
        }
    }
)


@dataclass(frozen=True, slots=True)
class YearTariffs:
    """Tariffs of one project for one calendar year."""

    year: int
    fixed_monthly: dict[str, float]
    variable: dict[str, float]

    @property
    def fixed_monthly_total(self) -> float:
        """Sum of all fixed monthly costs."""
        return round(sum(self.fixed_monthly.values()), 2)


@dataclass(frozen=True, slots=True)
class Project:
    """An Eteck project with its tariffs per year."""

    key: str
    name: str
    years: dict[int, YearTariffs]

    def tariffs_for(self, year: int) -> YearTariffs:
        """Return the tariffs for a year.

        Falls back to the most recent earlier year when the year itself has
        not been added yet, or the earliest known year before that.
        """
        if year in self.years:
            return self.years[year]
        earlier = [known for known in self.years if known < year]
        return self.years[max(earlier) if earlier else min(self.years)]


def load_projects(path: Path = TARIFFS_FILE) -> dict[str, Project]:
    """Load and validate all projects. Blocking; run in the executor."""
    with path.open(encoding="utf-8") as file:
        data = _SCHEMA(yaml.safe_load(file) or {})
    return {
        key: Project(
            key=key,
            name=project["name"],
            years={
                year: YearTariffs(
                    year=year,
                    fixed_monthly=tariffs[FIXED_MONTHLY],
                    variable=tariffs[VARIABLE],
                )
                for year, tariffs in project["years"].items()
            },
        )
        for key, project in data.items()
    }
