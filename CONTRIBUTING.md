# Contributing

## Adding a project or a new year of tariffs

All tariffs live in one file:
[`custom_components/eteck/tariffs.yaml`](custom_components/eteck/tariffs.yaml).
You only need the "Product- en tarievenblad" for your project, which you can
download from the Eteck website or customer portal.

Not comfortable making a pull request? Open a
[Tariffs issue](https://github.com/desyncdotdev/home-assistant-eteck-tarieven/issues/new?template=tariffs.yml)
with the PDF attached and a maintainer will add it.

Using an AI agent? Give it the PDF and point it at [AGENTS.md](AGENTS.md).

```yaml
keijzershof-en-tuindershof-pijnacker-nootdorp:   # project key
  name: Keijzershof en Tuindershof, Pijnacker-Nootdorp
  years:
    2026:
      fixed_monthly:
        heat_pump_rental: 14.88
        metering: 2.81
        cooling: 18.18
        heating: 51.31
      variable:
        heating_per_gj: 40.97
        hot_water_per_m3: 6.88
```

Rules:

- **Project key**: the project name in lowercase with spaces replaced by `-`
  and other punctuation (such as commas) dropped. Never rename an existing key;
  installations refer to it.
- **`name`**: the project name exactly as printed on the tariff sheet.
- **`years`**: one entry per calendar year. Add a new year below the existing
  ones; keep the old years.
- Amounts are in EUR **including VAT**, with a `.` as decimal separator.
- Leave out the "Overige kosten" section.
- Leave out lines your project does not have.

| Key | Line on the tariff sheet |
| --- | --- |
| `fixed_monthly.heat_pump_rental` | Gebruik Warmtepomp/Afleverset |
| `fixed_monthly.metering` | Meettarief |
| `fixed_monthly.cooling` | Vaste kosten Koude |
| `fixed_monthly.heating` | Vaste kosten Warmte |
| `variable.heating_per_gj` | Levering ruimteverwarming per GJ |
| `variable.hot_water_per_m3` | Opwarming tapwater per m³ |

If your sheet has a line under "Vaste kosten" or "Variabele kosten" that is not
in this table, open an issue (attach the sheet) or add the key to `const.py`,
`translations/*.json` and this table.

Also update the project table in `README.md` (new row for a new project, the
years column for a new year). Attach the PDF to your pull request so the values
can be checked.

Run `mise run test` to validate the file; CI runs the same check on your pull
request.

## Pull requests

Pull requests are squash-merged, so the **PR title** must be a
[Conventional Commit](https://www.conventionalcommits.org). It ends up in the
changelog. For example:

- `feat(tariffs): add Keijzershof en Tuindershof 2027`
- `feat(tariffs): add project Example, City`
- `fix(tariffs): correct heating price for Example 2026`

Do not change the version number or `CHANGELOG.md`; release-please does that.
