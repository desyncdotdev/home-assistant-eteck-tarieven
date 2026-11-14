<p align="center">
   <img width="982" height="337" alt="afbeelding" src="https://github.com/user-attachments/assets/082676dc-0fbb-4a5a-a1c7-ba44ccb684d1" />
</p>

# Eteck for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

Home Assistant integration that exposes the tariffs of your
[Eteck](https://www.eteck.nl) heat network as sensors, so you can use them on
dashboards and as price entities in the Energy dashboard.

Eteck publishes a fixed tariff sheet per project per year. Those values live in
[`custom_components/eteck/tariffs.yaml`](custom_components/eteck/tariffs.yaml);
nothing is fetched from the internet.

> This is a community project and is not affiliated with or endorsed by Eteck.

## Supported projects

| Project | Years |
| --- | --- |
| Keijzershof en Tuindershof, Pijnacker-Nootdorp | 2026 |

Is your project or a new year missing? Adding it is a small YAML change, see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Installation

1. In HACS, open the menu → **Custom repositories**, add
   `https://github.com/desyncdotdev/home-assistant-eteck-tarieven` with type **Integration**.
2. Install **Eteck** and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, search for
   **Eteck** and choose your project.

## Sensors

All amounts are in EUR including VAT. Only the sensors your project has tariffs
for are created.

| Sensor | Unit | Tariff sheet |
| --- | --- | --- |
| Heat pump rental | EUR/month | Gebruik Warmtepomp/Afleverset |
| Metering fee | EUR/month | Meettarief |
| Fixed costs cooling | EUR/month | Vaste kosten Koude |
| Fixed costs heating | EUR/month | Vaste kosten Warmte |
| Total fixed costs | EUR/month | Sum of the above |
| Heating price | EUR/GJ | Levering ruimteverwarming per GJ |
| Hot water price | EUR/m³ | Opwarming tapwater per m³ |

The sensors follow the calendar year and switch to the new tariffs on 1 January.
If the new year has not been added yet, the latest known tariffs stay in use,
the `tariff_year` attribute shows which year they are from, and a repair
notification is raised.

## Development

Tooling is managed with [mise](https://mise.jdx.dev):

```sh
mise install      # Python and uv
mise run test     # tests, including validation of tariffs.yaml
mise run lint     # ruff
mise run format
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org);
releases are cut by [release-please](https://github.com/googleapis/release-please).
