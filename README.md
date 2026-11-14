<p align="center">
   <img width="982" height="337" alt="Ye-KVuzPoajF21V9" src="https://github.com/user-attachments/assets/fc7beb22-de58-4d44-b06a-3e9e17d99f61" />
</p>

# Eteck Tariffs for Home Assistant

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
   `https://github.com/desyncdotdev/home-assistant-eteck-tariffs` with type **Integration**.
2. Install **Eteck Tariffs** and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, search for
   **Eteck Tariffs** and choose your project.

## Sensors

All amounts are in EUR including VAT. Only the sensors your project has tariffs
for are created.

| Sensor | Unit | Tariff sheet |
| --- | --- | --- |
| Heat pump rental per month | EUR | Gebruik Warmtepomp/Afleverset |
| Metering fee per month | EUR | Meettarief |
| Fixed costs cooling per month | EUR | Vaste kosten Koude |
| Fixed costs heating per month | EUR | Vaste kosten Warmte |
| Total fixed costs per month | EUR | Sum of the above |
| Accumulated … (one per fixed cost, plus the total) | EUR | The fixed costs charged so far |
| Heating price | EUR/GJ | Levering ruimteverwarming per GJ |
| Hot water price | EUR/m³ | Opwarming tapwater per m³ |

## Cost calculations

- **Heating price** and **Hot water price** can be picked in the Energy
  dashboard as *Use an entity with current price* for your heat meter and your
  hot water meter. Home Assistant converts the price if your heat meter reports
  in kWh or MJ instead of GJ.
- The **Accumulated …** sensors are running totals in EUR: one for every fixed
  cost and one for all of them together, so you can pick the ones that apply to
  you. They start at 0 when you add the integration and grow every hour by that
  hour's share of the monthly amount, so each calendar month adds exactly the
  monthly amount. Time that
  Home Assistant was not running is caught up on start. Use them in statistics
  cards, utility meters and templates.

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
