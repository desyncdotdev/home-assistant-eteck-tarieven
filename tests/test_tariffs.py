"""Validate the bundled tariffs.yaml and the lookup logic."""

import pytest
import voluptuous as vol

from custom_components.eteck.tariffs import load_projects

PROJECT = "keijzershof-en-tuindershof-pijnacker-nootdorp"


def test_bundled_tariffs_are_valid():
    """The shipped file passes schema validation and has usable data."""
    projects = load_projects()
    assert projects
    for project in projects.values():
        for tariffs in project.years.values():
            assert tariffs.fixed_monthly or tariffs.variable


def test_keijzershof_2026():
    project = load_projects()[PROJECT]
    assert project.name == "Keijzershof en Tuindershof, Pijnacker-Nootdorp"
    tariffs = project.years[2026]
    assert tariffs.fixed_monthly == {
        "heat_pump_rental": 14.88,
        "metering": 2.81,
        "cooling": 18.18,
        "heating": 51.31,
    }
    assert tariffs.variable == {"heating_per_gj": 40.97, "hot_water_per_m3": 6.88}
    assert tariffs.fixed_monthly_total == 87.18


def test_year_fallback():
    project = load_projects()[PROJECT]
    assert project.tariffs_for(2026).year == 2026
    assert project.tariffs_for(2030).year == 2026
    assert project.tariffs_for(2020).year == 2026


@pytest.mark.parametrize(
    "content",
    [
        "Bad Key:\n  name: x\n  years: {2026: {}}",
        "with,-comma:\n  name: x\n  years: {2026: {}}",
        "ok:\n  years: {2026: {}}",
        "ok:\n  name: x\n  years: {}",
        "ok:\n  name: x\n  years: {2026: {variable: {unknown: 1}}}",
        "ok:\n  name: x\n  years: {2026: {fixed_monthly: {heating: -1}}}",
        "ok:\n  name: x\n  years: {2026: {fixed_monthly: {heating: '51,31'}}}",
    ],
)
def test_invalid_files_are_rejected(tmp_path, content):
    path = tmp_path / "tariffs.yaml"
    path.write_text(content)
    with pytest.raises(vol.Invalid):
        load_projects(path)
