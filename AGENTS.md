# Agent notes

- Home Assistant custom integration (`custom_components/eteck`), distributed via HACS.
- Tariff updates only touch `custom_components/eteck/tariffs.yaml` (and the project
  table in `README.md` for new projects). Follow `CONTRIBUTING.md` exactly.
- Validate with `mise run test` and `mise run lint` before committing.
- Use Conventional Commits. Never edit `CHANGELOG.md`, `.release-please-manifest.json`
  or the `version` in `manifest.json`; release-please owns them.
